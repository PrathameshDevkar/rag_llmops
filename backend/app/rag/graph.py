from langgraph.graph import StateGraph, START, END
from backend.app.rag.state import RAGState  
from backend.app.rag.nodes import retrieval_node, generate_node

def build_graph(checkpointer):
        
    graph=StateGraph(RAGState)

    graph.add_node("retrieval_node",retrieval_node)
    graph.add_node("generate_node",generate_node)

    graph.add_edge(START,"retrieval_node")
    graph.add_edge("retrieval_node","generate_node")
    graph.add_edge("generate_node",END)

    return graph.compile(checkpointer=checkpointer)

