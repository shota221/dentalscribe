from typing import Dict, Any, Optional, List
from chalicelib.models.job import Job
from chalicelib.clients.aws import AWSClients
from chalicelib.enums.job import JobStatus, JobType


class JobRepository:
    @staticmethod
    def find(job_id: str):
        return Job.find({Job.partition_key_name(): {"S": job_id}})

    @staticmethod
    def find_by_job_type(job_type: JobType) -> List[Dict[str, Any]]:
        index_name = "job_type-index"
        return Job.filter(
            index_name, {"job_type": {"S": job_type.value}}
        )
    
    @staticmethod
    def find_by_parent_job_id(parent_job_id: str) -> List[Dict[str, Any]]:
        index_name = "parent_job_id-index"
        return Job.filter(
            index_name, {"parent_job_id": {"S": parent_job_id}}
        )
    
    @staticmethod
    def increment_child_job_count(job_id: str, child_job_status: JobStatus):
        job = Job.find({Job.partition_key_name(): {"S": job_id}})
        if not job:
            raise Exception(f"Job not found: {job_id}")
        
        if not job.total_child_jobs:
            raise Exception(f"Job has no child jobs: {job_id}")
        
        client = AWSClients().get_dynamodb()

        if child_job_status == JobStatus.COMPLETED:
            update_expression = "SET completed_child_jobs = completed_child_jobs + :val"
        elif child_job_status == JobStatus.FAILED:
            update_expression = "SET failed_child_jobs = failed_child_jobs + :val"
        else:
            raise Exception(f"Invalid child job status: {child_job_status}")
        
        expression_attribute_values = {":val": {"N": "1"}}

        return client.update_item(
            table_name=Job.table_name(),
            key={Job.partition_key_name(): {"S": job_id}},
            update_expression=update_expression,
            expression_attribute_values=expression_attribute_values
        )