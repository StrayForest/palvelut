from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_promotion_workflow_reuses_exact_release_coordinates_without_rebuild():
    workflow = (ROOT / ".github/workflows/p5-promote.yml").read_text()

    assert "environment: staging" in workflow
    assert "environment: production" in workflow
    assert "needs: staging" in workflow
    assert workflow.count("PALVELUT_IMAGE: ${{ inputs.image }}") == 3
    assert workflow.count("PALVELUT_RELEASE: ${{ inputs.release }}") == 3
    assert workflow.count("bash infra/scripts/deploy-production.sh deploy") == 2
    assert "ghcr\\.io/strayforest/palvelut@sha256:" in workflow
    assert "docker build" not in workflow
    assert "docker tag" not in workflow
    assert "docker push" not in workflow
    assert ":latest" not in workflow


def test_promotion_is_serial_and_production_waits_for_staging():
    workflow = (ROOT / ".github/workflows/p5-promote.yml").read_text()

    assert "group: palvelut-release-promotion" in workflow
    assert "cancel-in-progress: false" in workflow
    staging_index = workflow.index("  staging:")
    production_index = workflow.index("  production:")
    assert staging_index < production_index
    assert workflow.index("    needs: staging", production_index) > production_index
