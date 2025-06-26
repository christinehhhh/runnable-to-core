import React from 'react'
import ReactFlow, { Background, Controls, Node, Edge } from 'reactflow'
import 'reactflow/dist/style.css'

interface FlowDiagramProps {
  nodes: Node[]
  edges: Edge[]
}

const FlowDiagram = ({ nodes, edges }: FlowDiagramProps) => (
  <div style={{ width: '100%', height: 500 }}>
    <ReactFlow
      nodes={nodes}
      edges={edges}
      fitView
      nodesDraggable={false}
      nodesConnectable={false}
      elementsSelectable={false}
      zoomOnScroll={false}
      panOnScroll
    >
      <Background />
      <Controls />
    </ReactFlow>
  </div>
)

export default FlowDiagram
