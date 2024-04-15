from st_supabase_connection import SupabaseConnection
import streamlit as st

# * Connection to Supabase
supabase_client = st.connection(
    name="supabase",
    type=SupabaseConnection,
)

# * Used to count the number of tokens used in a session
total_tokens_used = {
    "input_tok": 0,
    "output_tok": 0,
}
