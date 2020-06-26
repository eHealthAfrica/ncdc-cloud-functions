import logging
import json
from ast import literal_eval
from ckanapi import RemoteCKAN
from ckanapi import errors as ckanapi_errors

CKAN_DEFAULT_ORG = 'eHA'


class CKANInstance():

    def __init__(self, config):
        self.ckan = RemoteCKAN(**config)
        self.log = logging.getLogger('CKAN')
        self.log.setLevel(logging.DEBUG)
        self.bad_terms = []

    def create_dataset(self, dataset):
        dataset_name = dataset.get('name').lower()
        org_name = dataset.get('owner_org', CKAN_DEFAULT_ORG).lower()
        # ckan allows only lower case dataset names
        dataset.update({
            'name': dataset_name,
            'owner_org': org_name
        })

        try:
            self.ckan.action.organization_show(id=org_name)
        except ckanapi_errors.NotFound:
            self.log.debug(f'Creating {org_name} organization')
            try:
                org = {
                    'name': org_name,
                    'state': 'active',
                }
                self.ckan.action.organization_create(**org)
                self.log.debug(f'Successfully created {org_name} organization')
            except ckanapi_errors.ValidationError as e:
                self.log.error(f'Cannot create organization {org_name} \
                    because of the following errors: {json.dumps(e.error_dict)}')
                return
        except ckanapi_errors.ValidationError as e:
            self.log.error(
                f'Could not find {org_name} organization. {json.dumps(e.error_dict)}'
            )
            return

        try:
            return self.ckan.action.package_show(id=dataset_name)
        except ckanapi_errors.NotFound:
            # Dataset does not exist, so continue with execution to create it.
            pass

        try:
            new_dataset = self.ckan.action.package_create(**dataset)
            self.log.debug(f'Dataset {dataset_name} created in CKAN portal.')
            return new_dataset
        except ckanapi_errors.NotAuthorized as e:
            self.log.error(
                f'Cannot create dataset {dataset_name}. {str(e)}'
            )
        except ckanapi_errors.ValidationError as e:
            self.log.error(
                f'Cannot create dataset {dataset_name}. Payload is not valid. \
                    Check the following errors: {json.dumps(e.error_dict)}'
            )

    def create_resource(self, resource_name, dataset):
        try:
            resources = self.ckan.action.resource_search(query=f'name:{resource_name}')
            # todo: filter resource on dataset too
            if resources['count']:
                return resources['results'][0]
        except Exception:
            pass

        try:
            self.log.debug(f'Creating {resource_name} resource')
            resource = {
                'package_id': dataset.get('name'),
                'name': resource_name,
                'url_type': 'datastore',
            }
            new_resource = self.ckan.action.resource_create(**resource)
            self.log.debug(f'Successfully created {resource_name} resource')
            return new_resource
        except ckanapi_errors.NotAuthorized as e:
            self.log.error(f'Cannot create resource {resource_name}. {str(e)}')
        except ckanapi_errors.ValidationError as e:
            self.log.error(
                f'Cannot create resource {resource_name}. Payload is not valid. \
                    Check the following errors: {json.dumps(e.error_dict)}'
            )

    def create_resource_in_datastore(self, resource):
        payload = {
            'resource_id': resource.get('id'),
        }

        try:
            self.ckan.action.datastore_create(**payload)
        except ckanapi_errors.CKANAPIError as e:
            self.log.error(
                f'An error occurred while creating resource \
                {resource.get("name")} in Datastore. {str(e)}'
            )

    def send_data_to_datastore(self, fields, records, resource):
        resource_id = resource.get('id')
        resource_name = resource.get('name')
        payload = {
            'id': resource_id,
            'limit': 1,
        }

        try:
            response = self.ckan.action.datastore_search(**payload)
        except ckanapi_errors.CKANAPIError as e:
            self.log.error(
                f'An error occurred while getting Datastore fields for resource \
                {resource_id}. {str(e)}'
            )
            return

        new_fields = response.get('fields')
        new_fields[:] = [
            field for field in new_fields if field.get('id') != '_id'
        ]

        schema_changes = self.get_schema_changes(new_fields, fields)

        if len(new_fields) == 0 or len(schema_changes) > 0:
            self.log.info('Datastore detected schema changes')
            for new_field in schema_changes:
                new_fields.append(new_field)

            payload = {
                'resource_id': resource_id,
                'fields': new_fields,
            }

            try:
                self.ckan.action.datastore_create(**payload)
            except ckanapi_errors.CKANAPIError as cke:
                self.log.error(
                    f'An error occurred while adding new fields for resource \
                    {resource_name} in Datastore.'
                )
                label = str(cke)
                self.log.error(
                    'ResourceType: {0} Error: {1}'
                    .format(resource_name, label)
                )
                bad_fields = literal_eval(label).get('fields', None)
                if not isinstance(bad_fields, list):
                    raise ValueError('Bad field could not be identified.')
                issue = bad_fields[0]
                bad_term = str(issue.split(' ')[0]).strip("'").strip('"')
                self.bad_terms.append(bad_term)
                self.log.info(
                    'Recovery from error: bad field name %s' % bad_term)
                self.log.info('Reverting %s' % (schema_changes,))
                for new_field in schema_changes:
                    new_fields.remove(new_field)
                return self.send_data_to_datastore(fields, records, resource)

        records = self.convert_item_to_array(records, new_fields)

        payload = {
            'resource_id': resource_id,
            'method': 'insert',
            'records': records,
        }

        try:
            self.ckan.action.datastore_upsert(**payload)
            self.log.info(f'Updated resource {resource_id} in {self.ckan.address}.')
        except ckanapi_errors.CKANAPIError as cke:
            self.log.error(
                f'An error occurred while inserting data into resource {resource_name}'
            )
            self.log.error(
                f'ResourceType: {resource} Error: {str(cke)}'
            )

    def get_schema_changes(self, schema, fields):
        ''' Only check if new field has been added. '''

        new_fields = []

        for field in fields:
            field_found = False

            for schema_field in schema:
                if field.get('id') == schema_field.get('id'):
                    field_found = True
                    break

            if not field_found:
                if field.get('id') in self.bad_terms:
                    new_fields.append(self.rename_field(field))
                else:
                    new_fields.append(field)

        return new_fields

    def rename_field(self, field):
        bad_name = field.get('id')
        new_name = 'ae' + bad_name
        self.rename_fields[bad_name] = new_name
        field['id'] = new_name
        return field

    def convert_item_to_array(self, records, new_fields):
        ''' If a field is of type array, and the value for it contains a
        primitive type, then convert it to an array of that primitive type.

        This mutation is required for all records, otherwise CKAN will raise
        an exception.

        Example:
            For given field which is of type array of integers
            {'type': '_int', 'id': 'scores'}
            Original record {'scores': 10}
            Changed record {'scores': [10]}
        '''

        array_fields = []
        records = records[:]

        for field in new_fields:
            if field.get('type').startswith('_'):
                array_fields.append(field.get('id'))

        for record in records:
            for key, value in record.items():
                if self.bad_terms:
                    name = self.rename_fields.get(key, key)
                    if name != key:
                        del record[key]
                else:
                    name = key
                if key in array_fields:
                    record[name] = [value]
                else:
                    record[name] = value

        return records