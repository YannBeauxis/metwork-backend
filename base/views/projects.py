# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from base.models import SampleAnnotationProject
from base.views.model_auth import ModelAuthViewSet, IsOwnerOrPublic
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import FileResponse, HttpResponse
from rest_framework.parsers import JSONParser
from wsgiref.util import FileWrapper
from django.http import JsonResponse
import os, json


class ProjectSerializer(serializers.ModelSerializer):
    frag_sample = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = SampleAnnotationProject
        fields = (
            "name",
            "description",
            "user_name",
            "user_id",
            "public",
            "frag_sample",
            "status_code",
            "reaction_ids",
            "REACTIONS_LIMIT",
            "DEPTH_LIMIT",
            "annotation_init_ids",
            "molecules_matching_count",
            "molecules_all_count",
            "frag_compare_conf_id",
            "list_custom_frag_param_files",
        )


class ProjectViewSet(ModelAuthViewSet):
    permission_classes = (IsOwnerOrPublic,)
    serializer_class = ProjectSerializer

    def get_queryset(self):
        if self.action == "list":
            list_filter = self.request.query_params.get("filter", None)
            if list_filter == "public":
                return SampleAnnotationProject.objects.filter(public=True).order_by(
                    "-id"
                )
            else:
                return SampleAnnotationProject.objects.filter(
                    user=self.request.user
                ).order_by("-id")
        else:
            return SampleAnnotationProject.objects.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"])
    def clone_project(self, request, pk=None):
        project = self.get_object()
        try:
            clone = project.clone_project()
            return Response({"clone_id": clone.id})
        except:
            return Response({"error": "error while cloning project"})

    @action(detail=True, methods=["patch"])
    def update_frag_sample(self, request, pk=None):
        from fragmentation.models import FragSample

        project = self.get_object()
        data = JSONParser().parse(request)
        fs = FragSample.objects.get(id=data["frag_sample_id"])
        if fs.user == self.request.user:
            project.update_frag_sample(fs)
        return Response(ProjectSerializer(project).data)

    @action(detail=True, methods=["post"])
    def load_custom_frag_file(self, request, pk=None):
        project = self.get_object()
        req_data = request.data
        file_type = req_data["file_format"]
        file_data = request.data["file_data"].read().decode("utf-8")
        project.load_custom_frag_param_files(file_type, file_data)
        return Response(ProjectSerializer(project).data)

    @action(detail=True, methods=["post"])
    def delete_custom_frag_param_files(self, request, pk=None):
        project = self.get_object()
        data = JSONParser().parse(request)
        file_type = data["file_format"]
        project.delete_custom_frag_param_files(file_type)
        project.refresh_from_db()
        return Response(ProjectSerializer(project).data)

    # To delete ???
    @action(detail=True, methods=["get"])
    def reactions(self, request, pk=None):
        from metabolization.views import ReactionSerializer

        project = self.get_object()
        return Response({"first_test": "ok"})
        # return Response(ReactionSerializer(project.reactions_conf.reactions.all()).data)

    def change_item(self, self_, request, func):
        project = self_.get_object()
        data = JSONParser().parse(request)
        dataLabel = data["dataLabel"]
        if "item_ids" in data:
            getattr(project, func)(dataLabel, data["item_ids"])
        else:
            getattr(project, func)(dataLabel)
        return Response({"project_id": project.id})

    @action(detail=True, methods=["patch"])
    def add_items(self, request, pk=None):
        return self.change_item(self, request, "add_items")

    @action(detail=True, methods=["patch"])
    def add_all(self, request, pk=None):
        return self.change_item(self, request, "add_all")

    @action(detail=True, methods=["patch"])
    def remove_all(self, request, pk=None):
        return self.change_item(self, request, "remove_all")

    @action(detail=True, methods=["patch"])
    def remove_item(self, request, pk=None):
        return self.change_item(self, request, "remove_item")

    @action(detail=True, methods=["patch"])
    def select_reactions_by_tag(self, request, pk=None):
        project = self.get_object()
        project.select_reactions_by_tag()
        return Response({"project_id": project.id})

    @action(detail=True, methods=["patch"])
    def update_frag_compare_conf(self, request, pk=None):
        project = self.get_object()
        params = JSONParser().parse(request)
        project.update_conf("frag_compare_conf", params)
        return Response({"frag_compare_conf": project.frag_compare_conf.id})

    @action(detail=True, methods=["post"])
    def start_run(self, request, pk=None):
        project = self.get_object()
        project.save()
        project.run()
        return Response({"status_code": project.status_code})

    @action(detail=True, methods=["post"])
    def stop_run(self, request, pk=None):
        project = self.get_object()
        project.finish_run()
        return Response({"status_code": project.status_code})

    @action(detail=True, methods=["get"])
    def download_file(self, request, pk=None):
        file = self.request.query_params.get("file", None)
        file_name = self.request.query_params.get("file_name", None)
        methods = {
            "annotations": "gen_annotations",
            "annotations_details": "gen_annotations_details",
            "metexplore": "gen_metexplore",
            "all_molecules": "gen_all_molecules",
        }
        project = self.get_object()
        fileAddress = project.item_path() + "/" + file_name
        if not os.path.isfile(fileAddress):
            getattr(project, methods[file])()
        json_data = json.dumps({"data": open(fileAddress, "r").read()})
        return JsonResponse(json_data, safe=False)

    @action(detail=True, methods=["get"])
    def metabolization_network(self, request, pk=None):
        force = request.query_params.get("force", "False")
        force = force.lower() == "true"
        project = self.get_object()
        data = project.get_metabolization_network(force=force, task=True)
        return JsonResponse(data, safe=False)
