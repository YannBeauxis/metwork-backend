from collections import defaultdict
from django.db.models import Q


class FilteredQueryset:
    def __init__(self, request, model):
        self.request = request
        self.queryset = model.objects.all()
        self.set_project_id()
        self.set_queryset()

    def set_project_id(self):
        self.project_id = self.request.query_params.get("filter[project_id]", None)

    def set_queryset(self):
        self.filter_init()
        self.filter_project_selection()
        self.filter_status()
        self.filter_other()

    def filter_init(self):
        pass

    def filter_project_selection(self):

        queryset = self.queryset

        project_id = self.project_id
        selected = self.request.query_params.get("filter[selected]", None)
        if project_id:
            from base.models import SampleAnnotationProject

            queryset_ = SampleAnnotationProject.objects.get(id=project_id)
            if selected == "selected":
                queryset = self.get_all(queryset_)
            elif selected == "notselected":
                queryset = self.get_notselected(queryset_)
            else:
                queryset = self.get_default(queryset_)

        self.queryset = queryset

    def get_default(self, queryset_):
        return self.queryset

    def get_all(self, queryset_):
        return queryset_

    def get_notselected(self, queryset_):
        return queryset_

    def filter_status(self):

        filter_status = []

        for key, value in self.request.query_params.lists():
            if key == "filter[status][]":
                filter_status = [int(v) for v in value]
        if filter_status:
            self._filter_status(filter_status)

    def _filter_status(self, filter_status):
        self.queryset = self.queryset.filter(status_code__in=filter_status)

    def filter_other(self):

        pass
