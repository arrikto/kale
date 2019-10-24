import kfp


def list_experiments():
    c = kfp.Client()
    experiments = [e.name for e in c.list_experiments().experiments]
    return experiments
