"""GA4GH ServiceInfo Sidecar FastAPI application."""

from fastapi import FastAPI

from sidecar.api.routes.service_info import router as service_info_router

app = FastAPI(
    title="GA4GH ServiceInfo Sidecar",
    description=(
        "A reusable sidecar service that standardizes and exposes GA4GH ServiceInfo "
        "metadata across implementations such as DRS, TES, WES, TRS, and TESK."
    ),
    version="0.1.0",
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0",
    },
)

app.include_router(service_info_router)
