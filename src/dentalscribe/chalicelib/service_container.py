from chalicelib.services.job import JobService
from chalicelib.services.storage import StorageService
from chalicelib.services.voice2soap import Voice2SoapService

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

    @classmethod
    def get_voice2soap_service(cls):
        if cls._voice2soap_service is None:
            cls._voice2soap_service = Voice2SoapService()
        return cls._voice2soap_service
