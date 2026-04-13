from src.evaluation import STAGE_SPEC as EVALUATION_STAGE
from src.models import StageSpec
from src.patch_generation import STAGE_SPEC as PATCH_GENERATION_STAGE
from src.retrieval import STAGE_SPEC as RETRIEVAL_STAGE
from src.slicing import STAGE_SPEC as SLICING_STAGE
from src.symbolic_reasoning import STAGE_SPEC as SYMBOLIC_REASONING_STAGE

PIPELINE_STAGES: tuple[StageSpec, ...] = (
    RETRIEVAL_STAGE,
    PATCH_GENERATION_STAGE,
    SLICING_STAGE,
    SYMBOLIC_REASONING_STAGE,
    EVALUATION_STAGE,
)


def stage_keys() -> tuple[str, ...]:
    return tuple(stage.key for stage in PIPELINE_STAGES)
