from csv import reader


def csv_process_content_type(request):
    content_type = request.headers.get('Content-Type')
    if content_type == 'application/json':
        return request.get_json(silent=True)
    elif content_type.startswith('multipart/form-data'):
        if 'file' not in request.files:
            raise ValueError('No file provided.')
        rows = reader(
            request.files['file'].read().decode().split('\n'),
            delimiter=','
        )
        return [row for row in rows]


def csv_list_to_dict(data):
    result = []
    if data:
        headers = data.pop(0)
        for row in data:
            standardized_row = {}
            for header_index in range(len(headers)):
                standardized_row[headers[header_index]] = row[header_index]
            result.append(standardized_row)
    return result


def csv_list_to_xml(data):
    result = '<root xmlns:xsd="http://www.w3.org/2001/XMLSchema">'
    if data:
        headers = data.pop(0)
        for row in data:
            standardized_row = '<row>'
            for header_index in range(len(headers)):
                prop = headers[header_index]
                standardized_row += f'<{prop}>{row[header_index]}</{prop}>'
            result += standardized_row + '</row>'

    result += '</root>'
    return result
