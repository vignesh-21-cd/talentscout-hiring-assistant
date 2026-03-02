"""
TalentScout Hiring Assistant — UI styling and layout helpers.
All custom CSS, styled sections, and layout wrappers live here.
"""
import html
import streamlit as st

# ---------------------------------------------------------------------------
# Global styles
# ---------------------------------------------------------------------------

def apply_global_styles() -> None:
    """Inject custom CSS for background, typography, chat spacing, and cards."""
    st.markdown(
        """
        <style>
        /* Soft background */
        .stApp { background-color: #f5f7fa; }
        /* Main content padding and spacing */
        .block-container { padding: 1.5rem 2rem; max-width: 900px; }
        /* Larger title */
        h1 { font-size: 1.85rem !important; font-weight: 600 !important; margin-bottom: 0.25rem !important; }
        /* Section headers */
        h2 { font-size: 1.25rem !important; font-weight: 600 !important; margin-top: 1rem !important; }
        h3 { font-size: 1.1rem !important; font-weight: 600 !important; margin-top: 0.75rem !important; }
        /* Chat message spacing */
        [data-testid="stChatMessage"] { padding: 0.6rem 0; margin-bottom: 0.25rem; }
        /* Card containers for recruiter sections */
        .card { background: #fff; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); padding: 1.25rem; margin-bottom: 1rem; }
        .card pre { background: #f8f9fa; padding: 1rem; border-radius: 6px; overflow: auto; font-size: 0.9rem; }
        /* Sidebar */
        [data-testid="stSidebar"] { background: #fff; }
        [data-testid="stSidebar"] .block-container { padding: 1rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Layout helpers
# ---------------------------------------------------------------------------

def render_app_header(subtitle: str = "AI-powered initial screening assistant for technology roles.") -> None:
    """Render main app title, subtitle, and divider."""
    st.title("🤖 TalentScout Hiring Assistant")
    st.markdown(subtitle)
    st.divider()


def render_section(title: str, level: int = 2) -> None:
    """Render a section header and divider. level 2 = ##, level 3 = ###."""
    prefix = "#" * level
    st.markdown(f"{prefix} {title}")
    st.divider()


def render_card(title: str, content: str) -> None:
    """Render a styled card with title and preformatted content (content is escaped for HTML)."""
    escaped = html.escape(content)
    st.markdown(
        f"<div class='card'><h3>{html.escape(title)}</h3><pre>{escaped}</pre></div>",
        unsafe_allow_html=True,
    )
