collection = None


def metrics(mongodb):
    global collection
    collection = mongodb['metrics']

    return _metrics


def _metrics():
    return 'Metrics'
