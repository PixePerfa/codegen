import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Heading, 
  Spinner, 
  Text,
  Select,
  HStack,
  Button,
  useToast
} from '@chakra-ui/react';
import { symbolApi } from '../services/api';
import { Dependency } from '../types';
import { ForceGraph2D } from 'react-force-graph';

interface DependencyGraphProps {
  projectId: string;
  onNodeClick?: (node: any) => void;
}

interface GraphNode {
  id: string;
  name: string;
  type: string;
  file_path: string;
  val: number;
}

interface GraphLink {
  source: string;
  target: string;
  type: string;
}

const DependencyGraph: React.FC<DependencyGraphProps> = ({ projectId, onNodeClick }) => {
  const [dependencies, setDependencies] = useState<Dependency[]>([]);
  const [loading, setLoading] = useState(true);
  const [graphData, setGraphData] = useState<{ nodes: GraphNode[], links: GraphLink[] }>({ nodes: [], links: [] });
  const [filterType, setFilterType] = useState<string>('all');
  const toast = useToast();

  useEffect(() => {
    fetchDependencies();
  }, [projectId]);

  const fetchDependencies = async () => {
    try {
      setLoading(true);
      const response = await symbolApi.getDependencies(projectId);
      setDependencies(response.data);
      processGraphData(response.data);
    } catch (error) {
      console.error('Error fetching dependencies:', error);
      toast({
        title: 'Error fetching dependencies',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    } finally {
      setLoading(false);
    }
  };

  const processGraphData = (deps: Dependency[]) => {
    const nodes = new Map<string, GraphNode>();
    const links: GraphLink[] = [];

    // Create nodes
    deps.forEach(dep => {
      const sourceId = `${dep.source.name}-${dep.source.type}`;
      const targetId = `${dep.target.name}-${dep.target.type}`;

      if (!nodes.has(sourceId)) {
        nodes.set(sourceId, {
          id: sourceId,
          name: dep.source.name,
          type: dep.source.type,
          file_path: dep.source.file_path,
          val: 1
        });
      } else {
        const node = nodes.get(sourceId)!;
        node.val += 1;
        nodes.set(sourceId, node);
      }

      if (!nodes.has(targetId)) {
        nodes.set(targetId, {
          id: targetId,
          name: dep.target.name,
          type: dep.target.type,
          file_path: dep.target.file_path,
          val: 1
        });
      } else {
        const node = nodes.get(targetId)!;
        node.val += 1;
        nodes.set(targetId, node);
      }

      // Create link
      links.push({
        source: sourceId,
        target: targetId,
        type: `${dep.source.type}-${dep.target.type}`
      });
    });

    setGraphData({
      nodes: Array.from(nodes.values()),
      links
    });
  };

  const filterGraph = () => {
    if (filterType === 'all') {
      processGraphData(dependencies);
      return;
    }

    const filteredDeps = dependencies.filter(dep => {
      if (filterType === 'class') {
        return dep.source.type === 'CLASS' || dep.target.type === 'CLASS';
      } else if (filterType === 'function') {
        return dep.source.type === 'FUNCTION' || dep.target.type === 'FUNCTION';
      }
      return true;
    });

    processGraphData(filteredDeps);
  };

  useEffect(() => {
    filterGraph();
  }, [filterType, dependencies]);

  const handleNodeClick = (node: GraphNode) => {
    if (onNodeClick) {
      onNodeClick({
        name: node.name,
        type: node.type,
        file_path: node.file_path
      });
    }
  };

  if (loading) {
    return (
      <Box textAlign="center" py={8}>
        <Spinner />
        <Text mt={2}>Loading dependencies...</Text>
      </Box>
    );
  }

  return (
    <Box h="100%" display="flex" flexDirection="column">
      <HStack mb={4} spacing={4}>
        <Select 
          value={filterType} 
          onChange={(e) => setFilterType(e.target.value)}
          width="200px"
        >
          <option value="all">All Dependencies</option>
          <option value="class">Class Dependencies</option>
          <option value="function">Function Dependencies</option>
        </Select>
        <Button size="sm" onClick={fetchDependencies}>Refresh</Button>
      </HStack>

      {graphData.nodes.length === 0 ? (
        <Box textAlign="center" py={8}>
          <Text>No dependencies found</Text>
        </Box>
      ) : (
        <Box flex="1" borderWidth="1px" borderRadius="md">
          <ForceGraph2D
            graphData={graphData}
            nodeLabel={(node: any) => `${node.name} (${node.type})`}
            nodeColor={(node: any) => node.type === 'CLASS' ? '#8884d8' : '#82ca9d'}
            nodeRelSize={6}
            linkDirectionalArrowLength={3.5}
            linkDirectionalArrowRelPos={1}
            linkCurvature={0.25}
            onNodeClick={handleNodeClick}
            cooldownTicks={100}
            width={800}
            height={600}
          />
        </Box>
      )}
    </Box>
  );
};

export default DependencyGraph;