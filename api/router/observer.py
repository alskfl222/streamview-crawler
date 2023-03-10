import os
from subprocess import Popen, PIPE
import time
from fastapi import APIRouter
from pydantic import BaseModel


class Item(BaseModel):
    streamId: str


def observer_routing(sv):
    router = APIRouter()

    @router.post('')
    async def init(item: Item):
        if sv.sub_process:
            sv.sub_process.kill()
        command = ["python3", "observer.py", item.streamId]
        print(f"INIT OBSERVER : {item.streamId}")
        sv.sub_process = Popen(command, preexec_fn=lambda: os.setpgrp(),
                               stdout=PIPE, stderr=PIPE)
        time.sleep(3)
        return sv.sub_process.poll()

    @router.post("/alive")
    async def check():
        if sv.sub_process:
            return sv.sub_process.poll()
        else:
            return "No sub_process"

    @router.post("/stop")
    async def stop():
        if sv.sub_process:
            sv.sub_process.kill()
            # stdout, stderr = sv.sub_process.communicate()
            # return {"stdout": stdout, "stderr": stderr}
            return sv.sub_process.poll()
        else:
            return "No sub_process"

    sv.include_router(router, prefix="/observer")
