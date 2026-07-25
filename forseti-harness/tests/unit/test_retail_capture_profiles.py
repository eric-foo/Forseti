from __future__ import annotations

from pathlib import Path

import pytest

from runners import run_source_capture_cloakbrowser_packet as cloakbrowser_runner
from source_capture.retail_capture_profiles import (
    extract_amazon_asin_from_url,
    extract_amazon_search_query_from_url,
    extract_nordstrom_product_id_from_url,
    extract_retailer_product_identity_from_url,
    extract_retailer_variant_identity_from_url,
    extract_sephora_product_id_from_url,
    extract_target_grid_subject_from_url,
    extract_target_product_id_from_url,
    extract_target_search_query_from_url,
    extract_ulta_product_id_from_url,
    get_retail_capture_profile,
    merge_source_detail_sufficiency_requirements,
    retail_capture_profile_names,
    target_bestseller_grid_url,
    validate_retail_capture_profile_route,
)
from source_capture.source_detail_sufficiency import (
    SourceDetailSufficiencyRequirements,
    evaluate_source_detail_sufficiency,
)


def test_profiles_cover_each_retailer_and_page_kind_with_explicit_route_flags() -> None:
    profiles = [get_retail_capture_profile(name) for name in retail_capture_profile_names()]

    assert {profile.retailer for profile in profiles} == {
        "amazon",
        "luckyscent",
        "nordstrom",
        "revolve",
        "sephora",
        "ulta",
        "walmart",
        "target",
    }
    assert {profile.page_kind for profile in profiles} == {
        "grid_aggregate",
        "pdp_aggregate",
        "pdp_distribution",
    }
    assert {profile.source_surface for profile in profiles} == {
        "cloakbrowser_snapshot",
        "direct_http",
    }
    assert get_retail_capture_profile("ulta_grid_aggregate").ordinary_operation is True
    assert get_retail_capture_profile("walmart_grid_aggregate").source_surface == "direct_http"
    assert (
        get_retail_capture_profile("target_grid_aggregate").source_surface
        == "cloakbrowser_snapshot"
    )
    assert get_retail_capture_profile("sephora_pdp_aggregate").scroll_step_px == 350
    assert get_retail_capture_profile("luckyscent_pdp_aggregate").scroll_step_px == 500
    assert get_retail_capture_profile("luckyscent_pdp_aggregate").scroll_passes == 4
    assert get_retail_capture_profile("sephora_grid_aggregate").scroll_target_selector is None
    catalog = get_retail_capture_profile("sephora_catalog_grid_aggregate")
    assert catalog.scroll_step_px == 0
    assert catalog.scroll_passes == 0
    assert catalog.load_more_clicks == 0
    assert catalog.derive_target_sephora_catalog_from_url is True
    assert get_retail_capture_profile("sephora_pdp_aggregate").scroll_target_selector is None
    assert (
        get_retail_capture_profile("sephora_pdp_distribution").scroll_target_selector
        == "#ratings-reviews-container"
    )
    assert get_retail_capture_profile("ulta_pdp_aggregate").scroll_passes == 0
    assert get_retail_capture_profile("target_pdp_aggregate").settle_seconds == 6.0
    assert (
        get_retail_capture_profile("amazon_pdp_distribution").wait_until
        == "domcontentloaded"
    )
    assert get_retail_capture_profile("amazon_pdp_distribution").settle_seconds == 0.0
    assert get_retail_capture_profile("amazon_grid_aggregate").scroll_passes == 0
    assert get_retail_capture_profile("amazon_pdp_distribution").derive_target_asin_from_url is True
    assert get_retail_capture_profile("amazon_pdp_aggregate").derive_target_asin_from_url is True
    assert get_retail_capture_profile("amazon_grid_aggregate").derive_target_query_from_url is True
    assert get_retail_capture_profile("sephora_pdp_aggregate").derive_target_sephora_product_id_from_url is True
    assert get_retail_capture_profile("ulta_pdp_aggregate").derive_target_ulta_product_id_from_url is True
    assert get_retail_capture_profile("target_pdp_aggregate").derive_target_target_product_id_from_url is True
    assert get_retail_capture_profile(
        "target_grid_aggregate"
    ).derive_target_target_grid_subject_from_url is True
    nordstrom = get_retail_capture_profile("nordstrom_pdp_aggregate")
    assert nordstrom.wait_until == "domcontentloaded"
    assert nordstrom.scroll_passes == 1
    assert nordstrom.scroll_step_px == 500
    assert nordstrom.derive_target_nordstrom_product_id_from_url is True


def test_sephora_grid_profile_is_subject_agnostic_and_requires_grid_structure() -> None:
    profile = get_retail_capture_profile("sephora_grid_aggregate")
    requirements = profile.requirements_for_capture(
        url="https://www.sephora.com/brand/summer-fridays?country_switch=us"
    )

    assert all("Lip Sleeping Mask" not in value for value in requirements.visible_text_contains)
    assert profile.scroll_passes == 1
    assert profile.load_more_selector == "text=Show More Products"
    assert profile.load_more_clicks == 10
    assert profile.scroll_stop_condition() is None
    assert profile.metadata()["expected_route_flags"]["load_more_clicks"] == 10
    result = evaluate_source_detail_sufficiency(
        requirements=requirements,
        access_block_reason=None,
        visible_text=(
            "Summer Fridays 2 Results Quicklook Product One $24.00 "
            "Quicklook Product Two $42.00 1-2 of 2 Results"
        ),
        rendered_dom=(
            '<script id="linkStore" type="text/json">'
            '{"page":{"nthBrand":{"products":[{"productId":"P1"}],'
            '"totalProducts":2}}}</script>'
        ),
    )

    assert result.passed is True


def test_sephora_catalog_grid_profile_binds_bounded_page_and_bestseller_sort() -> None:
    profile = get_retail_capture_profile("sephora_catalog_grid_aggregate")
    url = (
        "https://www.sephora.com/shop/makeup-cosmetics?country_switch=us"
        "&lang=en&currentPage=2&sortBy=BEST_SELLING"
    )
    requirements = profile.requirements_for_capture(url=url)
    result = evaluate_source_detail_sufficiency(
        requirements=requirements,
        access_block_reason=None,
        visible_text=(
            "Makeup 2391 Results Sort by: Bestselling Quicklook Product $25.00 "
            "1-120 of 2391 Results"
        ),
        rendered_dom=(
            '<script>Sephora.renderQueryParams={"country":"US",'
            '"urlPath":"/shop/makeup-cosmetics",'
            '"cachedQueryParams":"currentPage=2&sortBy=BEST_SELLING"};</script>'
            '<div data-cnstrc-browse="true" data-cnstrc-num-results="2391">'
            '<a data-cnstrc-item-id="P000001"></a></div>'
        ),
    )

    assert result.passed is True
    assert profile.scroll_stop_condition() is None
    for invalid_url in (
        "https://www.sephora.com/shop/makeup-cosmetics?currentPage=13&sortBy=BEST_SELLING",
        "https://www.sephora.com/shop/makeup-cosmetics?currentPage=2&sortBy=NEW",
        "https://www.sephora.com/beauty/beauty-best-sellers?currentPage=2&sortBy=BEST_SELLING",
    ):
        with pytest.raises(ValueError, match="currentPage in \\[1,12\\]"):
            profile.requirements_for_capture(url=invalid_url)


@pytest.mark.parametrize(
    ("extractor", "url", "expected"),
    (
        (extract_sephora_product_id_from_url, "https://www.sephora.com/product/example-P123456", "P123456"),
        (extract_ulta_product_id_from_url, "https://www.ulta.com/p/example-pimprod2046225?sku=2645443", "pimprod2046225"),
        (extract_target_product_id_from_url, "https://www.target.com/p/example/-/A-80184023", "80184023"),
        (extract_target_search_query_from_url, "https://www.target.com/s?searchTerm=Summer%20Fridays", "Summer Fridays"),
    ),
)
def test_shallow_profiles_derive_the_commissioned_target_from_the_url(
    extractor, url: str, expected: str
) -> None:
    assert extractor(url) == expected


def test_retailer_identity_helpers_separate_product_from_selected_variant() -> None:
    sephora = (
        "https://www.sephora.com/product/cc-me-vitamin-c-serum-P449180"
        "?skuId=2224061&country_switch=us"
    )
    ulta = "https://www.ulta.com/p/almost-lipstick-VP11111?sku=2253011"

    assert extract_retailer_product_identity_from_url("sephora", sephora) == "P449180"
    assert extract_retailer_variant_identity_from_url("sephora", sephora) == "2224061"
    assert extract_retailer_product_identity_from_url("ulta", ulta) == "VP11111"
    assert extract_retailer_variant_identity_from_url("ulta", ulta) == "2253011"
    assert extract_retailer_product_identity_from_url("unknown", sephora) is None
    assert extract_retailer_variant_identity_from_url("amazon", sephora) is None


def test_target_grid_profile_binds_the_requested_search_query() -> None:
    profile = get_retail_capture_profile("target_grid_aggregate")
    visible_text = "Summer Fridays 12 results Guest Rating $24.00"
    admitted = evaluate_source_detail_sufficiency(
        requirements=profile.requirements_for_capture(
            url="https://www.target.com/s?searchTerm=Summer%20Fridays"
        ),
        access_block_reason=None,
        visible_text=visible_text,
        rendered_dom="<html>target product cards</html>",
    )
    mismatched = evaluate_source_detail_sufficiency(
        requirements=profile.requirements_for_capture(
            url="https://www.target.com/s?searchTerm=Another%20Brand"
        ),
        access_block_reason=None,
        visible_text=visible_text,
        rendered_dom="<html>target product cards</html>",
    )
    assert admitted.passed is True
    assert mismatched.passed is False


def test_target_grid_profile_binds_brand_and_normalizes_bestseller_start() -> None:
    profile = get_retail_capture_profile("target_grid_aggregate")
    url = "https://www.target.com/b/e-l-f/-/N-5oajg?sortBy=newest&count=96&Nao=24"
    requirements = profile.requirements_for_capture(url=url)
    result = evaluate_source_detail_sufficiency(
        requirements=requirements,
        access_block_reason=None,
        visible_text="e.l.f. 244 results Guest Rating $10.00",
        rendered_dom="<html>target product cards</html>",
    )

    unrelated_word = evaluate_source_detail_sufficiency(
        requirements=requirements,
        access_block_reason=None,
        visible_text="Bookshelf organizers 244 results Guest Rating $10.00",
        rendered_dom="<html>target product cards</html>",
    )

    assert result.passed is True
    assert unrelated_word.passed is False
    assert extract_target_grid_subject_from_url(url) == ("brand", "e-l-f")
    assert target_bestseller_grid_url(url) == (
        "https://www.target.com/b/e-l-f/-/N-5oajg?"
        "sortBy=bestselling&moveTo=product-list-grid"
    )


_SHALLOW_PDP_IDENTITY_CASES = (
    (
        "sephora_pdp_aggregate",
        "https://www.sephora.com/product/example-P420652",
        "https://www.sephora.com/product/other-P999999",
        "https://www.sephora.com/product/other-P42065",
        "Ratings & Reviews (1,234)\n$24.00\n",
        '<div id="linkStore">{"product":{"productId":"P420652"}}</div>',
    ),
    (
        "ulta_pdp_aggregate",
        "https://www.ulta.com/p/example-pimprod2046225?sku=2645443",
        "https://www.ulta.com/p/other-pimprod9999999?sku=2645443",
        "https://www.ulta.com/p/other-pimprod204622?sku=2645443",
        "Reviews\n1,204 Reviews\n$24.00\n",
        '<script>window.__APOLLO_STATE__={"aggregateRating":4.5,'
        '"availability":"InStock","id":"pimprod2046225"}</script>',
    ),
    (
        "target_pdp_aggregate",
        "https://www.target.com/p/example/-/A-80184023",
        "https://www.target.com/p/other/-/A-99999999",
        "https://www.target.com/p/other/-/A-16801840",
        "Pickup\nShipping\n4.5 out of 5 stars with 12 reviews\n$24.00\n",
        '<script id="__NEXT_DATA__">{"tcin":"80184023","ts":1680184023456}</script>',
    ),
)


@pytest.mark.parametrize(
    (
        "profile_name",
        "captured_url",
        "wrong_product_url",
        "contained_id_url",
        "visible_text",
        "rendered_dom",
    ),
    _SHALLOW_PDP_IDENTITY_CASES,
)
def test_shallow_pdp_profiles_bind_the_captured_products_own_id(
    profile_name: str,
    captured_url: str,
    wrong_product_url: str,
    contained_id_url: str,
    visible_text: str,
    rendered_dom: str,
) -> None:
    profile = get_retail_capture_profile(profile_name)

    def evaluate(url: str):
        return evaluate_source_detail_sufficiency(
            requirements=profile.requirements_for_capture(url=url),
            access_block_reason=None,
            visible_text=visible_text,
            rendered_dom=rendered_dom,
        )

    assert evaluate(captured_url).passed is True
    assert evaluate(wrong_product_url).passed is False
    # A requested id that merely occurs inside a longer id or numeric run on the
    # page is a different product, not the commissioned one.
    assert evaluate(contained_id_url).passed is False


@pytest.mark.parametrize(
    ("profile_name", "url", "message"),
    (
        (
            "sephora_pdp_aggregate",
            "https://www.sephora.com/product/example",
            "requires a Sephora product id",
        ),
        (
            "ulta_pdp_aggregate",
            "https://www.ulta.com/p/example",
            "requires an Ulta product id",
        ),
        (
            "target_pdp_aggregate",
            "https://www.target.com/p/example",
            "requires a Target TCIN",
        ),
        (
            "target_grid_aggregate",
            "https://www.target.com/s?searchTerm=%20",
            "requires a non-empty Target search query",
        ),
    ),
)
def test_shallow_profiles_refuse_a_url_without_a_derivable_target(
    profile_name: str, url: str, message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        get_retail_capture_profile(profile_name).requirements_for_capture(url=url)


@pytest.mark.parametrize(
    ("profile_name", "requested_url", "same_product_final_url", "wrong_product_final_url"),
    (
        (
            "amazon_pdp_aggregate",
            "https://www.amazon.com/dp/B012345678",
            "https://www.amazon.com/example/dp/B012345678?th=1",
            "https://www.amazon.com/dp/B987654321",
        ),
        (
            "nordstrom_pdp_aggregate",
            "https://www.nordstrom.com/s/example/1234567",
            "https://www.nordstrom.com/s/canonical-name/1234567?color=Black",
            "https://www.nordstrom.com/s/example/7654321",
        ),
        (
            "sephora_pdp_aggregate",
            "https://www.sephora.com/product/example-P420652",
            "https://www.sephora.com/product/canonical-name-P420652?skuId=1",
            "https://www.sephora.com/product/example-P999999",
        ),
        (
            "ulta_pdp_aggregate",
            "https://www.ulta.com/p/example-pimprod2046225?sku=2645443",
            "https://www.ulta.com/p/canonical-name-pimprod2046225?sku=2645443",
            "https://www.ulta.com/p/example-pimprod9999999?sku=2645443",
        ),
        (
            "target_pdp_aggregate",
            "https://www.target.com/p/example/-/A-80184023",
            "https://www.target.com/p/canonical-name/-/A-80184023?preselect=1",
            "https://www.target.com/p/example/-/A-99999999",
        ),
    ),
)
def test_pdp_profiles_require_the_final_route_to_retain_the_requested_product(
    profile_name: str,
    requested_url: str,
    same_product_final_url: str,
    wrong_product_final_url: str,
) -> None:
    profile = get_retail_capture_profile(profile_name)
    assert (
        cloakbrowser_runner._retail_target_identity_failure(
            retail_capture_profile=profile,
            requested_url=requested_url,
            final_url=same_product_final_url,
        )
        is None
    )
    failure = cloakbrowser_runner._retail_target_identity_failure(
        retail_capture_profile=profile,
        requested_url=requested_url,
        final_url=wrong_product_final_url,
    )
    assert failure is not None
    assert "final browser route encoded" in failure


def test_nordstrom_profile_binds_the_requested_product_id() -> None:
    profile = get_retail_capture_profile("nordstrom_pdp_aggregate")
    assert (
        extract_nordstrom_product_id_from_url(
            "https://www.nordstrom.com/s/the-lip-balm/8260802"
        )
        == "8260802"
    )
    requirements = profile.requirements_for_capture(
        url="https://www.nordstrom.com/s/the-lip-balm/8260802"
    )
    result = evaluate_source_detail_sufficiency(
        requirements=requirements,
        access_block_reason=None,
        visible_text=(
            "The Lip Balm\nNécessaire\n$28.00\nSold by Nordstrom\nReviews\n"
            "4.6 out of 5\n5 stars 81%\n4 stars 7%\n3 stars 3%\n"
            "2 stars 5%\n1 star 3%\n"
        ),
        rendered_dom=(
            '<a href="/s/the-lip-balm/8260802">The Lip Balm</a>'
            '<script type="application/ld+json">{"@type":"Product",'
            '"reviewCount":118}</script>'
        ),
    )
    assert result.passed is True

    wrong = profile.requirements_for_capture(
        url="https://www.nordstrom.com/s/another-product/9999999"
    )
    wrong_result = evaluate_source_detail_sufficiency(
        requirements=wrong,
        access_block_reason=None,
        visible_text=(
            "The Lip Balm\nNécessaire\n$28.00\nSold by Nordstrom\nReviews\n"
            "4.6 out of 5\n5 stars 81%\n4 stars 7%\n3 stars 3%\n"
            "2 stars 5%\n1 star 3%\n"
        ),
        rendered_dom=(
            '<a href="/s/the-lip-balm/8260802">The Lip Balm</a>'
            '<script type="application/ld+json">{"@type":"Product",'
            '"reviewCount":118}</script>'
        ),
    )
    assert wrong_result.passed is False


def test_amazon_distribution_profile_accepts_changing_values_but_requires_full_data() -> None:
    profile = get_retail_capture_profile("amazon_pdp_distribution")
    visible_text = """
LANEIGE Lip Sleeping Mask
New York 10001
Currently unavailable
71K+ bought in past month
$25.50
4.7 out of 5 stars
37,104 global ratings
5 star 80%
4 star 12%
3 star 5%
2 star 1%
1 star 2%
"""
    rendered_dom = """
<html><body>
<input name="currencyOfPreference" value="USD">
<input id="ASIN" value="B07XXPHQZK">
<a href="/gp/customer-reviews/R3V62VIIGMFTE3">Read more</a>
<div>1,500 customers mention moisturizing</div>
</body></html>
"""

    result = evaluate_source_detail_sufficiency(
        requirements=profile.requirements,
        access_block_reason=None,
        visible_text=visible_text,
        rendered_dom=rendered_dom,
    )

    assert result.passed is True

    missing_insights = evaluate_source_detail_sufficiency(
        requirements=profile.requirements,
        access_block_reason=None,
        visible_text=visible_text,
        rendered_dom=rendered_dom.replace("1,500 customers mention", "insights absent"),
    )
    assert missing_insights.passed is False
    assert any(
        "customers mention" in reason
        for reason in missing_insights.failure_reasons
    )


def test_extract_amazon_asin_from_url_reads_dp_and_gp_product_paths() -> None:
    assert (
        extract_amazon_asin_from_url("https://www.amazon.com/Laneige-Sleeping-Berry/dp/B07XXPHQZK")
        == "B07XXPHQZK"
    )
    assert (
        extract_amazon_asin_from_url("https://www.amazon.com/gp/product/B07TOWER28?ref=x")
        == "B07TOWER28"
    )
    assert extract_amazon_asin_from_url("https://www.amazon.com/s?k=lip+mask") is None


def test_amazon_distribution_profile_no_longer_hardcodes_a_laneige_identity_literal() -> None:
    profile = get_retail_capture_profile("amazon_pdp_distribution")

    assert "LANEIGE Lip Sleeping Mask" not in profile.requirements.visible_text_contains
    assert not any(
        "B07XXPHQZK" in pattern for pattern in profile.requirements.rendered_dom_regexes
    )


def test_amazon_distribution_profile_validates_the_captured_skus_own_asin() -> None:
    profile = get_retail_capture_profile("amazon_pdp_distribution")
    tower28_visible_text = """
Tower 28 Beauty SOS Rescue Spray
New York 10001
In Stock
12K+ bought in past month
$16.00
4.6 out of 5 stars
9,204 global ratings
5 star 78%
4 star 13%
3 star 5%
2 star 2%
1 star 2%
"""
    tower28_rendered_dom = """
<html><body>
<input name="currencyOfPreference" value="USD">
<input id="ASIN" value="B07TOWER28">
<a href="/gp/customer-reviews/R1TOWER28REVIEW">Read more</a>
<div>820 customers mention soothing</div>
</body></html>
"""

    requirements = profile.requirements_for_capture(
        url="https://www.amazon.com/Tower-28-Beauty-SOS-Rescue-Spray/dp/B07TOWER28",
    )
    result = evaluate_source_detail_sufficiency(
        requirements=requirements,
        access_block_reason=None,
        visible_text=tower28_visible_text,
        rendered_dom=tower28_rendered_dom,
    )
    assert result.passed is True

    wrong_sku_requirements = profile.requirements_for_capture(
        url="https://www.amazon.com/Some-Other-Product/dp/B0WRONGASN",
    )
    wrong_sku_result = evaluate_source_detail_sufficiency(
        requirements=wrong_sku_requirements,
        access_block_reason=None,
        visible_text=tower28_visible_text,
        rendered_dom=tower28_rendered_dom,
    )
    assert wrong_sku_result.passed is False
    assert any("B0WRONGASN" in reason for reason in wrong_sku_result.failure_reasons)


def test_amazon_distribution_profile_requires_a_derivable_asin_in_the_capture_url() -> None:
    profile = get_retail_capture_profile("amazon_pdp_distribution")

    with pytest.raises(ValueError, match="requires an Amazon ASIN"):
        profile.requirements_for_capture(url="https://www.amazon.com/s?k=lip+mask")


def test_amazon_pdp_aggregate_profile_no_longer_hardcodes_a_laneige_identity_literal() -> None:
    profile = get_retail_capture_profile("amazon_pdp_aggregate")

    assert "LANEIGE Lip Sleeping Mask" not in profile.requirements.visible_text_contains
    assert not any(
        "B07XXPHQZK" in pattern for pattern in profile.requirements.rendered_dom_regexes
    )


def test_amazon_pdp_aggregate_profile_validates_the_captured_skus_own_asin() -> None:
    profile = get_retail_capture_profile("amazon_pdp_aggregate")
    tower28_visible_text = """
Tower 28 Beauty SOS Rescue Spray
New York 10001
In Stock
12K+ bought in past month
$16.00
4.6 out of 5 stars
9,204 global ratings
"""
    tower28_rendered_dom = """
<html><body>
<input name="currencyOfPreference" value="USD">
<input id="ASIN" value="B07TOWER28">
<a href="/gp/customer-reviews/R1TOWER28REVIEW">Read more</a>
</body></html>
"""

    requirements = profile.requirements_for_capture(
        url="https://www.amazon.com/Tower-28-Beauty-SOS-Rescue-Spray/dp/B07TOWER28",
    )
    result = evaluate_source_detail_sufficiency(
        requirements=requirements,
        access_block_reason=None,
        visible_text=tower28_visible_text,
        rendered_dom=tower28_rendered_dom,
    )
    assert result.passed is True

    wrong_sku_requirements = profile.requirements_for_capture(
        url="https://www.amazon.com/Some-Other-Product/dp/B0WRONGASN",
    )
    wrong_sku_result = evaluate_source_detail_sufficiency(
        requirements=wrong_sku_requirements,
        access_block_reason=None,
        visible_text=tower28_visible_text,
        rendered_dom=tower28_rendered_dom,
    )
    assert wrong_sku_result.passed is False
    assert any("B0WRONGASN" in reason for reason in wrong_sku_result.failure_reasons)


def test_amazon_pdp_aggregate_profile_requires_a_derivable_asin_in_the_capture_url() -> None:
    profile = get_retail_capture_profile("amazon_pdp_aggregate")

    with pytest.raises(ValueError, match="requires an Amazon ASIN"):
        profile.requirements_for_capture(url="https://www.amazon.com/s?k=lip+mask")


def test_extract_amazon_search_query_from_url_reads_the_k_parameter() -> None:
    assert (
        extract_amazon_search_query_from_url("https://www.amazon.com/s?k=Tower+28+Beauty")
        == "Tower 28 Beauty"
    )
    assert (
        extract_amazon_search_query_from_url(
            "https://www.amazon.com/Laneige-Sleeping-Berry/dp/B07XXPHQZK"
        )
        is None
    )
    assert extract_amazon_search_query_from_url("https://www.amazon.com/s?k=") is None


def test_amazon_grid_aggregate_profile_no_longer_hardcodes_a_laneige_identity_literal() -> None:
    profile = get_retail_capture_profile("amazon_grid_aggregate")

    assert "LANEIGE Lip Sleeping Mask" not in profile.requirements.visible_text_contains
    assert not any(
        "B07XXPHQZK" in pattern for pattern in profile.requirements.rendered_dom_regexes
    )


def test_amazon_grid_aggregate_profile_validates_the_captured_search_query() -> None:
    profile = get_retail_capture_profile("amazon_grid_aggregate")
    tower28_visible_text = """
1-48 of 214 results for "Tower 28 Beauty"
New York 10001
Tower 28 Beauty SOS Rescue Spray
4.6 out of 5 stars (9.2K)
$16.00
12K+ bought in past month
"""

    requirements = profile.requirements_for_capture(
        url="https://www.amazon.com/s?k=Tower+28+Beauty",
    )
    result = evaluate_source_detail_sufficiency(
        requirements=requirements,
        access_block_reason=None,
        visible_text=tower28_visible_text,
        rendered_dom=(
            "<html><script>ue_sn = 'www.amazon.com'</script>"
            "<body>ordinary grid markup</body></html>"
        ),
    )
    assert result.passed is True

    wrong_query_requirements = profile.requirements_for_capture(
        url="https://www.amazon.com/s?k=Some+Other+Brand",
    )
    wrong_query_result = evaluate_source_detail_sufficiency(
        requirements=wrong_query_requirements,
        access_block_reason=None,
        visible_text=tower28_visible_text,
        rendered_dom="<html><body>ordinary grid markup</body></html>",
    )
    assert wrong_query_result.passed is False
    assert any(
        "Some" in reason and "Other" in reason and "Brand" in reason
        for reason in wrong_query_result.failure_reasons
    )


def test_amazon_grid_aggregate_profile_requires_a_derivable_search_query_in_the_capture_url() -> None:
    profile = get_retail_capture_profile("amazon_grid_aggregate")

    with pytest.raises(ValueError, match="requires a non-empty Amazon search query"):
        profile.requirements_for_capture(url="https://www.amazon.com/Laneige-Sleeping-Berry/dp/B07XXPHQZK")


def test_sephora_distribution_profile_accepts_current_color_prose_without_colon() -> None:
    profile = get_retail_capture_profile("sephora_pdp_distribution")
    visible_text = """
    Lip Sleeping Mask in Berry - 2.5g
    Highly Rated By Customers For: Satisfaction (57), Color (55), Sticky (50)
    Ratings & Reviews (3)
    Summary
    5 4 3 2 1 3
    Verified Purchases
    """

    result = evaluate_source_detail_sufficiency(
        requirements=profile.requirements,
        access_block_reason=None,
        visible_text=visible_text,
        rendered_dom="<html><body>current Sephora product detail</body></html>",
    )

    assert result.passed is True


def test_cloakbrowser_cli_uses_profile_wait_until_unless_operator_overrides(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    captured: list[dict[str, object]] = []

    def fake_run(**kwargs: object) -> tuple[int, str]:
        captured.append(kwargs)
        return 0, "packet"

    monkeypatch.setattr(
        cloakbrowser_runner,
        "run_source_capture_cloakbrowser_packet",
        fake_run,
    )
    base_args = [
        "--url",
        "https://www.amazon.com/Laneige-Sleeping-Berry/dp/B07XXPHQZK",
        "--source-family",
        "retail_pdp",
        "--source-surface",
        "cloakbrowser_snapshot",
        "--decision-question",
        "Did the Amazon profile capture its required data?",
        "--output",
        str(tmp_path / "packet"),
        "--retail-capture-profile",
        "amazon_pdp_distribution",
        "--delivery-zip",
        "10001",
    ]

    assert cloakbrowser_runner.main(base_args) == 0
    assert captured[-1]["wait_until"] == "domcontentloaded"
    assert captured[-1]["settle_seconds"] == 0.0

    assert cloakbrowser_runner.main([*base_args, "--wait-until", "load"]) == 0
    assert captured[-1]["wait_until"] == "load"


@pytest.mark.parametrize("name", retail_capture_profile_names())
def test_content_sparse_shell_fails_every_profile_without_transport_or_block_failure(
    name: str,
) -> None:
    profile = get_retail_capture_profile(name)

    result = evaluate_source_detail_sufficiency(
        requirements=profile.requirements,
        access_block_reason=None,
        visible_text="Be Right Back",
        rendered_dom="<html><body>Be Right Back</body></html>",
    )

    assert result.enabled is True
    assert result.passed is False
    assert result.failure_reasons


def test_profile_route_validation_fails_before_capture_on_wrong_host_or_rung() -> None:
    profile = get_retail_capture_profile("target_grid_aggregate")

    with pytest.raises(ValueError, match="requires hostname www.target.com"):
        validate_retail_capture_profile_route(
            profile,
            url="https://www.walmart.com/search?q=lip+mask",
            source_family="retail_pdp",
            source_surface="cloakbrowser_snapshot",
        )
    with pytest.raises(ValueError, match="requires source_surface cloakbrowser_snapshot"):
        validate_retail_capture_profile_route(
            profile,
            url="https://www.target.com/s?searchTerm=lip%20mask",
            source_family="retail_pdp",
            source_surface="direct_http",
        )


@pytest.mark.parametrize(
    ("profile_name", "pin_field", "pin_value"),
    (
        ("sephora_grid_aggregate", "sephora_market", "US"),
        ("sephora_catalog_grid_aggregate", "sephora_market", "US"),
        ("sephora_pdp_aggregate", "sephora_market", "US"),
        ("ulta_grid_aggregate", "ulta_market", "US"),
        ("ulta_pdp_aggregate", "ulta_market", "US"),
    ),
)
def test_shallow_ladder_profiles_require_their_exact_us_pin(
    profile_name: str, pin_field: str, pin_value: str
) -> None:
    kwargs = {"delivery_zip": None, "sephora_market": None, "ulta_market": None, "target_zip": None}
    profile = get_retail_capture_profile(profile_name)
    with pytest.raises(ValueError, match="shallow baseline requires"):
        cloakbrowser_runner._validate_retail_baseline_profile_request(
            retail_capture_profile=profile, **kwargs
        )
    kwargs[pin_field] = pin_value
    cloakbrowser_runner._validate_retail_baseline_profile_request(
        retail_capture_profile=profile, **kwargs
    )


def test_target_catalog_grid_does_not_require_a_requested_delivery_zip() -> None:
    cloakbrowser_runner._validate_retail_baseline_profile_request(
        retail_capture_profile=get_retail_capture_profile("target_grid_aggregate"),
        delivery_zip=None,
        sephora_market=None,
        ulta_market=None,
        target_zip=None,
    )


@pytest.mark.parametrize(
    ("profile_name", "delivery_zip", "target_zip"),
    (
        ("amazon_grid_aggregate", None, None),
        ("amazon_grid_aggregate", "90210", None),
        ("amazon_pdp_aggregate", None, None),
        ("amazon_pdp_aggregate", "90210", None),
        ("target_grid_aggregate", None, None),
        ("target_grid_aggregate", None, "90210"),
        ("target_pdp_aggregate", None, None),
        ("target_pdp_aggregate", None, "90210"),
    ),
)
def test_fulfillment_zip_is_optional_local_context_not_surface_admission(
    profile_name: str,
    delivery_zip: str | None,
    target_zip: str | None,
) -> None:
    cloakbrowser_runner._validate_retail_baseline_profile_request(
        retail_capture_profile=get_retail_capture_profile(profile_name),
        delivery_zip=delivery_zip,
        sephora_market=None,
        ulta_market=None,
        target_zip=target_zip,
    )


def test_admitted_grid_projection_output_is_required_locally_and_automatic_in_lake_mode(
    tmp_path: Path,
) -> None:
    target = get_retail_capture_profile("target_grid_aggregate")
    with pytest.raises(ValueError, match="target_grid_aggregate requires"):
        cloakbrowser_runner._validate_retail_grid_projection_request(
            retail_capture_profile=target, retail_grid_projection_output=None
        )
    cloakbrowser_runner._validate_retail_grid_projection_request(
        retail_capture_profile=target,
        retail_grid_projection_output=tmp_path / "target-grid.json",
    )
    cloakbrowser_runner._validate_retail_grid_projection_request(
        retail_capture_profile=target,
        retail_grid_projection_output=None,
        data_root_mode=True,
    )
    with pytest.raises(ValueError, match="forbidden in --data-root mode"):
        cloakbrowser_runner._validate_retail_grid_projection_request(
            retail_capture_profile=target,
            retail_grid_projection_output=tmp_path / "target-grid.json",
            data_root_mode=True,
        )
    amazon = get_retail_capture_profile("amazon_grid_aggregate")
    with pytest.raises(ValueError, match="amazon_grid_aggregate requires"):
        cloakbrowser_runner._validate_retail_grid_projection_request(
            retail_capture_profile=amazon,
            retail_grid_projection_output=None,
        )
    cloakbrowser_runner._validate_retail_grid_projection_request(
        retail_capture_profile=amazon,
        retail_grid_projection_output=tmp_path / "amazon-grid.json",
    )
    cloakbrowser_runner._validate_retail_grid_projection_request(
        retail_capture_profile=amazon,
        retail_grid_projection_output=None,
        data_root_mode=True,
    )


def test_profile_requirements_merge_with_explicit_requirements_without_weakening_either() -> None:
    explicit = SourceDetailSufficiencyRequirements(
        min_visible_text_bytes=100,
        visible_text_contains=("operator marker",),
    )
    profile = get_retail_capture_profile("sephora_pdp_aggregate")

    merged = merge_source_detail_sufficiency_requirements(explicit, profile.requirements)

    assert merged is not None
    assert merged.require_not_access_blocked is True
    assert merged.min_visible_text_bytes == 100
    assert merged.visible_text_contains == (
        "operator marker",
        "Ratings & Reviews",
    )


def test_ulta_grid_profile_is_subject_agnostic_and_owns_bounded_continuation() -> None:
    profile = get_retail_capture_profile("ulta_grid_aggregate")
    requirements = profile.requirements_for_capture(
        url="https://www.ulta.com/brand/clinique"
    )

    assert profile.ordinary_operation is True
    assert profile.load_more_selector == "button.LoadContent__button"
    assert profile.load_more_clicks == 10
    assert profile.scroll_stop_condition() is None
    result = evaluate_source_detail_sufficiency(
        requirements=requirements,
        access_block_reason=None,
        visible_text="Clinique Add to bag $18.00 You have viewed 3 of 3",
        rendered_dom=(
            '<html><script>window.__APP_LOCALE__="en-US"</script>'
            '<ul data-test="products-list">'
            '<li data-test="products-list-item">Clinique</li></ul></html>'
        ),
    )

    assert result.passed is True


def test_ulta_category_grid_profile_delegates_continuation_to_page_traversal() -> None:
    profile = get_retail_capture_profile("ulta_category_grid_aggregate")

    assert profile.ordinary_operation is True
    assert profile.wait_until == "domcontentloaded"
    assert profile.scroll_passes == 0
    assert profile.load_more_selector is None
    assert profile.load_more_clicks == 0
