from symbiotic_swe.evaluation import STAGE_SPEC as EVALUATION_STAGE
from symbiotic_swe.models import StageSpec
from symbiotic_swe.patch_generation import STAGE_SPEC as PATCH_GENERATION_STAGE
from symbiotic_swe.retrieval import STAGE_SPEC as RETRIEVAL_STAGE
from symbiotic_swe.slicing import STAGE_SPEC as SLICING_STAGE
from symbiotic_swe.symbolic_reasoning import STAGE_SPEC as SYMBOLIC_REASONING_STAGE

PIPELINE_STAGES: tuple[StageSpec, ...] = (
    RETRIEVAL_STAGE,
    PATCH_GENERATION_STAGE,
    SLICING_STAGE,
    SYMBOLIC_REASONING_STAGE,
    EVALUATION_STAGE,
)


def stage_keys() -> tuple[str, ...]:
    return tuple(stage.key for stage in PIPELINE_STAGES)
