
from core.logging import logger
from fastapi import APIRouter, HTTPException
from kubernetes.executor import KubectlError, get_executor
from models.schemas import InvestigationRequest, InvestigationResponse
from services.history import get_history_service
from services.investigation import run_investigation

router = APIRouter()


@router.get("/clusters")
async def list_clusters():
    """List available Kubernetes clusters from kubeconfig."""
    logger.info("Listing available Kubernetes clusters")
    try:
        executor = get_executor()
        clusters_result = executor.get_clusters()
        current_result = executor.get_current_context()

        if "error" in clusters_result:
            raise HTTPException(status_code=500, detail=clusters_result.get("error", "Failed to list clusters"))

        clusters = clusters_result.get("raw_output", "").strip().split("\n") if clusters_result.get("raw_output") else []
        current_context = current_result.get("raw_output", "").strip() if current_result.get("raw_output") else None

        # Get all contexts with their cluster names
        contexts_result = executor.run(["config", "get-contexts", "-o", "name"], parse_json=False)
        context_names = contexts_result.get("raw_output", "").strip().split("\n") if contexts_result.get("raw_output") else []

        # Build cluster info with context names
        cluster_info = []
        for cluster in clusters:
            if not cluster.strip():
                continue
            cluster_name = cluster.strip()
            # Find context name for this cluster
            context_name = None
            for ctx in context_names:
                if cluster_name in ctx:
                    context_name = ctx
                    break

            cluster_info.append({
                "name": cluster_name,
                "context_name": context_name,
                "current": cluster_name in (current_context or "")
            })

        return {
            "status": "success",
            "clusters": cluster_info,
            "current_context": current_context,
        }
    except KubectlError as e:
        logger.error(f"Failed to list clusters: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list clusters: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to list clusters: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list clusters: {str(e)}")


@router.post("/clusters/{context_name}/use")
async def use_cluster(context_name: str):
    """Switch to a different Kubernetes cluster context."""
    logger.info(f"Switching to cluster context: {context_name}")
    try:
        executor = get_executor()
        result = executor.use_context(context_name)

        if "error" in result:
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to switch context"))

        return {
            "status": "success",
            "message": f"Switched to context: {context_name}",
            "current_context": context_name,
        }
    except KubectlError as e:
        logger.error(f"Failed to switch context: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to switch context: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to switch context: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to switch context: {str(e)}")


@router.post("/investigate", response_model=InvestigationResponse)
async def investigate_cluster(request: InvestigationRequest):
    """Run Kubernetes investigation and return structured evidence."""
    logger.info(f"Investigation requested for namespace: {request.namespace or 'all'}, context: {request.context or 'current'}")

    try:
        result = run_investigation(request.namespace, request.context)

        # Save to history
        history_service = get_history_service()
        history_service.save(result)

        return {
            "status": "success",
            "investigation": result,
        }
    except Exception as e:
        logger.error(f"Investigation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Investigation failed: {str(e)}")


@router.get("/investigations/history")
async def get_investigation_history(limit: int = 50):
    """Get investigation history."""
    logger.info("Fetching investigation history")
    try:
        history_service = get_history_service()
        history = history_service.get_all(limit)
        return {
            "status": "success",
            "history": history,
        }
    except Exception as e:
        logger.error(f"Failed to fetch history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch history: {str(e)}")


@router.get("/investigations/{investigation_id}")
async def get_investigation(investigation_id: str):
    """Get a specific investigation by ID."""
    logger.info(f"Fetching investigation: {investigation_id}")
    try:
        history_service = get_history_service()
        investigation = history_service.get_by_id(investigation_id)
        if not investigation:
            raise HTTPException(status_code=404, detail="Investigation not found")
        return {
            "status": "success",
            "investigation": investigation,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch investigation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch investigation: {str(e)}")


@router.get("/investigate")
async def investigate_cluster_get():
    """Health check for investigate endpoint."""
    return {"message": "Use POST /investigate to run investigation"}
