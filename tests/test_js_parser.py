from __future__ import annotations

from mon.parsers import js_parser as jp


def test_brace_matching_ignores_braces_inside_strings_and_comments() -> None:
    sample = '''
    function outer() {
        // a { comment brace
        const s = "a } string brace";
        const t = `template ${ 1 + 1 } literal`;
        return 1;
    }
    '''
    open_index = sample.index("{")
    close_index = jp.find_matching_close_brace(sample, open_index)
    assert close_index is not None
    assert sample[close_index] == "}"
    assert sample[open_index:close_index + 1].strip().endswith("}")
    assert sample.count("{", open_index, close_index) >= 1


def test_extract_function_snippet_finds_innermost_enclosing_function() -> None:
    sample = """
    export async function outer(id) {
        return await fetch('/api/outer/' + id);
    }
    class Api {
        async inner() {
            return await fetch('/api/inner');
        }
    }
    """
    inner_index = sample.index("fetch('/api/inner')")
    snippet = jp.extract_function_snippet(sample, inner_index)
    assert snippet.function_name == "inner"
    assert "outer" not in snippet.code.split("\n")[0]


def test_name_agnostic_wrapper_detection() -> None:
    sample = """
    async function fundWallet() {
        const xk9q = await auegj("/wallet/fund", { amount: 500 });
        if (!xk9q.status) { return; }
        console.log(xk9q.data.wallet.balance);
    }
    """
    call_sites = jp.find_call_sites(sample)
    assert len(call_sites) == 1
    assert call_sites[0].wrapper_function_name == "auegj"
    assert call_sites[0].endpoint_path == "/wallet/fund"
    assert call_sites[0].http_method == "POST"


def test_multi_library_detection() -> None:
    sample = """
    axios.get("/api/ping");
    ky.post("/api/status", {json: {a: 1}});
    superagent.delete("/api/item/1");
    $.ajax({ url: "/api/legacy", method: "PUT" });
    xhr.open("GET", "/api/data");
    """
    styles = {c.call_style for c in jp.find_call_sites(sample)}
    assert styles == {"axios", "ky", "superagent", "jquery_ajax", "xhr"}


def test_branch_split_and_dotted_schema() -> None:
    function_body = """
    async function check() {
        const res = await fetch("/x");
        const data = await res.json();
        if (!data.ok) { console.log(data.error); return; }
        console.log(data.payload.items);
        data.payload.items.map(i => i.id);
    }
    """
    branches = jp.split_success_error_branches(function_body)
    assert branches.detected
    names = jp.detect_response_variable_names(function_body)
    assert "data" in names
    pattern = jp.build_dotted_path_pattern(names)
    schema = jp.build_schema(branches.success_branch, pattern)
    assert schema["payload"]["items"] == ["TYPE_ARRAY_OF_OBJECTS"]


def test_navigation_target_detection() -> None:
    sample = """
    window.location.href = "/dashboard";
    window.location = "/dashboard/settings";
    router.push("/profile");
    history.pushState({}, "", "/checkout/success");
    """
    targets = set(jp.find_navigation_targets(sample))
    assert targets == {"/dashboard", "/dashboard/settings", "/profile", "/checkout/success"}
