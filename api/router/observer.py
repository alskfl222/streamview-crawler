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
        if sv.observer:
            stdout, stderr = sv.observer.communicate()
            print({"stdout": stdout, "stderr": stderr})
            sv.observer.kill()
        command = ["python3", "observer.py", item.streamId]
        print(f"INIT OBSERVER : {item.streamId}")
        sv.observer = Popen(command, preexec_fn=lambda: os.setpgrp(),
                               stdout=PIPE, stderr=PIPE)
        time.sleep(3)
        return sv.observer.poll()

    @router.post("/alive")
    async def check():
        if sv.observer:
            return sv.observer.poll()
        else:
            return "No observer"

    @router.post("/stop")
    async def stop():
        if sv.observer:
            sv.observer.kill()
            # stdout, stderr = sv.observer.communicate()
            # return {"stdout": stdout, "stderr": stderr}
            return sv.observer.poll()
        else:
            return "No sub_process"

    sv.include_router(router, prefix="/observer")
