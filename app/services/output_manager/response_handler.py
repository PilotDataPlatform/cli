
from app.services.output_manager.error_handler import SrvErrorHandler, ECustomizedError

class HPCJobInfoResponse:

    def __init__(self, payload: dict, response: dict):
        self.payload = payload
        self.res = response

    def return_200_response(self):
        pass

    def return_400_response(self):
        error_msg = self.res.get("error_msg")
        host = self.payload.get('host')
        if 'HPC protocal required' in error_msg:
            error_detail = f"missing protocol in the host, try http://{host} or https://{host}"
        else:
            error_detail = "Cannot get job, please verify your job ID and try again later"
        SrvErrorHandler.customized_handle(ECustomizedError.CANNOT_PROCESS_HPC_JOB, True, value=error_detail)

    def return_404_response(self):
        error_msg = self.res.get('error_msg')
        job_id = self.payload.get('job_id')
        host = self.payload.get('host')
        if 'Job ID' in error_msg:
            error_detail = f'job {job_id} may not exist'
        elif 'Host not found' in error_msg:
            error_detail = f'host {host} may not exist'
        SrvErrorHandler.customized_handle(ECustomizedError.CANNOT_PROCESS_HPC_JOB, True, value=error_detail)

    def return_500_response(self):
        job_id = self.payload.get('job_id')
        error_detail = f'Job ID {job_id}'
        SrvErrorHandler.customized_handle(ECustomizedError.CANNOT_PROCESS_HPC_JOB, True, value=error_detail)


class HPCJobSubmitResponse:

    def __init__(self, payload: dict, response: dict) -> None:
        self.payload = payload
        self.res = response

    def return_200_response(self):
        pass

    def return_400_response(self):
        error_msg = self.res.get('error_msg')
        host = self.payload.get('host')
        if 'Missing script' in error_msg:
            error_detail = f"{error_msg} in the job json file"
        elif 'HPC protocal required' in error_msg:
            error_detail = f"missing protocol in the host, try http://{host} or https://{host}"
        else:
            error_detail = "Cannot submit job, please verify your json file and try again later"
        SrvErrorHandler.customized_handle(ECustomizedError.CANNOT_PROCESS_HPC_JOB, True, value=error_detail)

    def return_403_response(self):
        error_detail = self.res.get('error_msg')
        SrvErrorHandler.customized_handle(ECustomizedError.CANNOT_PROCESS_HPC_JOB, True, value=error_detail)

    def return_500_response(self):
        path = self.payload.get('path')
        error_detail = f'submit job {path}'
        SrvErrorHandler.customized_handle(ECustomizedError.CANNOT_PROCESS_HPC_JOB, True, value=error_detail)


class HPCListPartitionsResponse:
    def __init__(self) -> None:
        pass