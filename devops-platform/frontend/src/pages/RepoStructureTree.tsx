import React from 'react';
import { Folder, File, ChevronRight, ChevronDown } from 'lucide-react';
import { RepoNode } from '../utils/api';
import './RepoStructureTree.css';

interface Props {
  data: RepoNode[];
  descriptions: Record<string, string>;
  depth?: number;
}

export default function RepoStructureTree({ data, descriptions, depth = 0 }: Props) {
  return (
    <div className="repo-tree" style={{ marginLeft: depth > 0 ? '24px' : '0' }}>
      {data.map((node) => (
        <TreeNode key={node.path} node={node} descriptions={descriptions} depth={depth} />
      ))}
    </div>
  );
}

function TreeNode({ node, descriptions, depth }: { node: RepoNode; descriptions: Record<string, string>; depth: number }) {
  const [isOpen, setIsOpen] = React.useState(true);
  const hasChildren = node.children && node.children.length > 0;
  const description = descriptions[node.path];

  const getIcon = () => {
    if (node.type === 'tree' || node.type === 'dir') {
      return (
        <div className="node-icon node-icon--folder">
          <Folder size={14} />
        </div>
      );
    }
    return (
      <div className="node-icon node-icon--file">
        <File size={14} />
      </div>
    );
  };

  return (
    <div className="node-wrapper">
      <div className={`node-row ${node.type === 'tree' ? 'node-row--dir' : 'node-row--file'}`}>
        <div className="node-main">
          {hasChildren && (
            <button className="node-toggle" onClick={() => setIsOpen(!isOpen)}>
              {isOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
            </button>
          )}
          {!hasChildren && <div className="node-spacer" />}
          
          {getIcon()}
          
          <span className="node-name">{node.name}</span>
          
          {node.type === 'tree' && <span className="node-slash">/</span>}
        </div>

        {description && (
          <div className="node-description animate-fade-in">
            <div className="node-connector" />
            <span className="node-description-text">{description}</span>
          </div>
        )}
      </div>

      {isOpen && hasChildren && (
        <div className="node-children">
          <div className="tree-line" style={{ left: '11px' }} />
          <RepoStructureTree data={node.children!} descriptions={descriptions} depth={depth + 1} />
        </div>
      )}
    </div>
  );
}
