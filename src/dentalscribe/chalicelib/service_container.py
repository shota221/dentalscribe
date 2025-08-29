from chalicelib.services.job import JobService
from chalicelib.services.storage import StorageService

class ServiceContainer:
    _storage_service = None
    _job_service = None
    _voice2soap_service = None


    @classmethod
    def get_storage_service(cls):
        if cls._storage_service is None:
            cls._storage_service = StorageService()
        return cls._storage_service

    @classmethod
    def get_job_service(cls):
        if cls._job_service is None:
            cls._job_service = JobService()
        return cls._job_service
