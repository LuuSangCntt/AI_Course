import streamlit as st
import asyncio
import json
from mcp import ClientSession
from mcp.client.sse import sse_client
from openai import OpenAI
from contextlib import AsyncExitStack

# --- CẤU HÌNH ---
with open("SSE\A-Client\servers_config.json", "r") as f:
    CONFIG = json.load(f)

llm_client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")

st.set_page_config(page_title="Multi-Server AI Agent", layout="wide")
st.title("🚀 MCP Multi-Server Agent (with Debug Log)")
# 1. KHỞI TẠO KẾT NỐI (Chỉ chạy một lần khi load app)
if "mcp_data" not in st.session_state:
    st.session_state.mcp_data = {"tools": [], "active_sessions": {}, "status": {}}

async def init_mcp_servers():
    """Hàm này chỉ chạy 1 lần để kết nối tất cả server"""
    st.session_state.mcp_data["tools"] = []
    
    # Chúng ta dùng một stack toàn cục để giữ kết nối không bị đóng
    stack = AsyncExitStack()
    st.session_state.stack = stack 

    for s_cfg in CONFIG["mcp_servers"]:
        if not s_cfg.get("enabled", True): continue
        try:
            context = await stack.enter_async_context(sse_client(s_cfg["url"]))
            read, write = context
            session = await stack.enter_async_context(ClientSession(read, write))
            await session.initialize()
            
            tools_resp = await session.list_tools()
            for t in tools_resp.tools:
                st.session_state.mcp_data["tools"].append({
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": f"[{s_cfg['name']}] {t.description}",
                        "parameters": t.inputSchema
                    },
                    "server_session": session
                })
            st.session_state.mcp_data["status"][s_cfg['name']] = "✅ Online"
        except Exception as e:
            st.session_state.mcp_data["status"][s_cfg['name']] = f"❌ Offline: {str(e)}"

# Nút bấm để kết nối lại thủ công nếu cần
if st.sidebar.button("🔄 Refresh All MCP Connections"):
    asyncio.run(init_mcp_servers())

# Hiển thị trạng thái server ở sidebar cho gọn
for name, stat in st.session_state.mcp_data["status"].items():
    st.sidebar.write(f"**{name}**: {stat}")

# --- LOGIC CHAT ---
async def run_agent(user_input):
    all_tools = st.session_state.mcp_data["tools"]
    if not all_tools:
        return "Chưa có server nào online. Vui lòng kiểm tra sidebar."

    openai_tools = [{k: v for k, v in t.items() if k != 'server_session'} for t in all_tools]
    messages = [{"role": "user", "content": user_input}]
    
    response = llm_client.chat.completions.create(
        model="qwen3-14b",
        messages=messages,
        tools=openai_tools
    )
    
    ai_msg = response.choices[0].message
    if ai_msg.tool_calls:
        messages.append(ai_msg)
        for tool_call in ai_msg.tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            target_tool = next(t for t in all_tools if t["function"]["name"] == name)
            
            # Thực thi tool trên session đã mở sẵn
            result = await target_tool["server_session"].call_tool(name, args)
            messages.append({"role": "tool", "tool_call_id": tool_call.id, "name": name, "content": str(result.content)})

        final_res = llm_client.chat.completions.create(model="qwen3-14b", messages=messages)
        return final_res.choices[0].message.content
    return ai_msg.content
if "messages" not in st.session_state:
    st.session_state.messages = []

# Hiển thị lịch sử chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


if prompt := st.chat_input("Hỏi tôi về toán hoặc database..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response_text = asyncio.run(run_agent(prompt))
        st.markdown(response_text)
        st.session_state.messages.append({"role": "assistant", "content": response_text})