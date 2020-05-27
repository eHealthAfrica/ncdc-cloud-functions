def adder(request):
    x = int(request.args.get('x'))
    y = int(request.args.get('y'))
    return str(x + y)
