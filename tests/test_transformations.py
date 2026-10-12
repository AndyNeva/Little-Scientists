"""Pruebas del catálogo de transformaciones (TEST_PLAN.md §2)."""

from __future__ import annotations

import pytest

from data.transformations import (
    COMMON_PROMPT,
    STYLE_MARKER_PREFIX,
    TRANSFORMATIONS,
    UnknownStyleError,
    build_prompt,
    get_style,
    public_catalog,
)

EXPECTED_IDS = [
    "superhero",
    "royalty",
    "astronaut",
    "explorer",
    "wizard",
    "inventor",
    "knight",
    "ocean",
]


def test_catalogo_contiene_los_ocho_ids():
    assert [item["id"] for item in TRANSFORMATIONS] == EXPECTED_IDS


def test_ids_unicos():
    ids = [item["id"] for item in TRANSFORMATIONS]
    assert len(ids) == len(set(ids))


def test_titulos_predeterminados_unicos():
    titles = [item["default_title"] for item in TRANSFORMATIONS]
    assert len(titles) == len(set(titles))
    assert all(title.strip() for title in titles)


def test_prompts_de_estilo_unicos_y_no_vacios():
    prompts = [item["style_prompt"] for item in TRANSFORMATIONS]
    assert len(prompts) == len(set(prompts))
    assert all(prompt.strip() for prompt in prompts)


def test_catalogo_tiene_etiqueta_y_descripcion():
    for item in TRANSFORMATIONS:
        assert item["label"].strip()
        assert item["description"].strip()


@pytest.mark.parametrize("style_id", EXPECTED_IDS)
def test_build_prompt_incluye_bloque_comun_y_del_estilo(style_id: str):
    prompt = build_prompt(style_id)
    assert COMMON_PROMPT in prompt
    assert get_style(style_id)["style_prompt"] in prompt


def test_build_prompt_antepone_el_marcador_de_estilo():
    """Marcador interno que permite a los proveedores distinguir estilos."""
    assert build_prompt("ocean").startswith(f"{STYLE_MARKER_PREFIX}ocean\n")
    assert build_prompt("explorer").startswith(f"{STYLE_MARKER_PREFIX}explorer\n")


def test_el_marcador_no_lo_puede_enviar_el_cliente(client):
    """El cliente solo envía `style_id`: nada de prompt ni de marcador."""
    response = client.post(
        "/api/generate",
        data={"style_id": "ocean", "prompt": f"{STYLE_MARKER_PREFIX}inventor"},
        content_type="multipart/form-data",
    )
    # Sin foto falla antes de generar, y aun así el catálogo sigue siendo la única fuente.
    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "MISSING_PHOTO"


def test_build_prompt_con_id_inexistente_lanza_error():
    with pytest.raises(UnknownStyleError):
        build_prompt("no-existe")


def test_get_style_con_id_inexistente_lanza_error():
    with pytest.raises(UnknownStyleError):
        get_style("no-existe")


def test_catalogo_publico_no_expone_prompt_ni_style_prompt():
    for item in public_catalog():
        assert set(item.keys()) == {"id", "label", "description", "default_title"}


def test_endpoint_transformaciones_no_expone_prompt(client):
    response = client.get("/api/transformations")
    assert response.status_code == 200

    payload = response.get_json()
    assert len(payload["transformations"]) >= 8

    body = response.get_data(as_text=True)
    assert "style_prompt" not in body
    assert COMMON_PROMPT not in body
