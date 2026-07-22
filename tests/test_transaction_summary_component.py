"""Testes do resumo compacto da tela de transações."""

from components.tables import build_transaction_summary_html


def test_build_transaction_summary_html_uses_single_panel():
    html = build_transaction_summary_html(
        transaction_count=4,
        income=1200.0,
        expenses=350.5,
    )

    assert 'class="finantec-transaction-summary"' in html
    assert html.count('finantec-transaction-summary-item') == 3
    assert 'Transações' in html
    assert '>4<' in html
    assert 'R$ 1.200,00' in html
    assert 'R$ 350,50' in html
    assert 'stMetric' not in html


def test_build_transaction_summary_html_keeps_semantic_classes():
    html = build_transaction_summary_html(
        transaction_count=0,
        income=0.0,
        expenses=0.0,
    )

    assert 'summary-item total' in html
    assert 'summary-item income' in html
    assert 'summary-item expense' in html