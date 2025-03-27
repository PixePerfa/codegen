import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Heading,
  Text,
  Spinner,
  Alert,
  AlertIcon,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Select,
  HStack,
  Button,
  useToast,
  useColorModeValue,
} from '@chakra-ui/react';
import { projectApi } from '../services/api';
import * as d3 from 'd3';

interface CodeVisualizationProps {
  projectId: string;
  filePath?: string;
  onNodeClick?: (filePath: string) => void;
}

const CodeVisualization: React.FC<CodeVisualizationProps> = ({ 
  projectId, 
  filePath,
  onNodeClick 
}) => {
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [visualizations, setVisualizations] = useState<any>(null);
  const [selectedVisualization, setSelectedVisualization] = useState<string>('dependency_graph');
  const svgRef = useRef<SVGSVGElement>(null);
  const toast = useToast();
  
  const bgColor = useColorModeValue('white', 'gray.800');
  const textColor = useColorModeValue('gray.800', 'white');

  useEffect(() => {
    const loadVisualizations = async () => {
      try {
        setLoading(true);
        const response = await projectApi.getVisualizations(projectId, filePath);
        setVisualizations(response.data.result);
        setError(null);
      } catch (err) {
        setError('Failed to load visualizations');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    loadVisualizations();
  }, [projectId, filePath]);

  useEffect(() => {
    if (visualizations && selectedVisualization === 'dependency_graph') {
      renderDependencyGraph();
    } else if (visualizations && selectedVisualization === 'complexity_heatmap') {
      renderComplexityHeatmap();
    }
  }, [visualizations, selectedVisualization]);

  const renderDependencyGraph = () => {
    if (!svgRef.current || !visualizations?.dependency_graph) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const width = svgRef.current.clientWidth;
    const height = 600;

    const data = visualizations.dependency_graph;
    
    // Create a force simulation
    const simulation = d3.forceSimulation(data.nodes)
      .force("link", d3.forceLink(data.links).id((d: any) => d.id).distance(100))
      .force("charge", d3.forceManyBody().strength(-300))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("x", d3.forceX(width / 2).strength(0.1))
      .force("y", d3.forceY(height / 2).strength(0.1));

    // Create a container for the graph
    const container = svg.append("g");

    // Add zoom behavior
    svg.call(
      d3.zoom()
        .scaleExtent([0.1, 4])
        .on("zoom", (event) => {
          container.attr("transform", event.transform);
        })
    );

    // Create links
    const link = container.append("g")
      .selectAll("line")
      .data(data.links)
      .enter()
      .append("line")
      .attr("stroke", "#999")
      .attr("stroke-opacity", 0.6)
      .attr("stroke-width", (d: any) => Math.sqrt(d.value || 1));

    // Create node groups
    const node = container.append("g")
      .selectAll(".node")
      .data(data.nodes)
      .enter()
      .append("g")
      .attr("class", "node")
      .call(
        d3.drag()
          .on("start", dragstarted)
          .on("drag", dragged)
          .on("end", dragended)
      )
      .on("click", (event, d: any) => {
        if (onNodeClick && d.file_path) {
          onNodeClick(d.file_path);
        }
      });

    // Add circles to nodes
    node.append("circle")
      .attr("r", (d: any) => getNodeSize(d))
      .attr("fill", (d: any) => getNodeColor(d))
      .attr("stroke", "#fff")
      .attr("stroke-width", 1.5);

    // Add labels to nodes
    node.append("text")
      .attr("dx", 12)
      .attr("dy", ".35em")
      .text((d: any) => d.name)
      .style("font-size", "10px")
      .style("fill", textColor);

    // Add titles for tooltips
    node.append("title")
      .text((d: any) => `${d.name}\nType: ${d.type}\nFile: ${d.file_path}`);

    // Update positions on each tick
    simulation.on("tick", () => {
      link
        .attr("x1", (d: any) => d.source.x)
        .attr("y1", (d: any) => d.source.y)
        .attr("x2", (d: any) => d.target.x)
        .attr("y2", (d: any) => d.target.y);

      node
        .attr("transform", (d: any) => `translate(${d.x},${d.y})`);
    });

    // Drag functions
    function dragstarted(event: any, d: any) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }

    function dragged(event: any, d: any) {
      d.fx = event.x;
      d.fy = event.y;
    }

    function dragended(event: any, d: any) {
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }

    // Helper functions
    function getNodeSize(node: any) {
      switch (node.type) {
        case 'class': return 10;
        case 'function': return 7;
        case 'module': return 12;
        default: return 5;
      }
    }

    function getNodeColor(node: any) {
      switch (node.type) {
        case 'class': return '#ff9800';
        case 'function': return '#2196f3';
        case 'module': return '#4caf50';
        default: return '#9c27b0';
      }
    }
  };

  const renderComplexityHeatmap = () => {
    if (!svgRef.current || !visualizations?.complexity_heatmap) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const width = svgRef.current.clientWidth;
    const height = 600;
    const margin = { top: 50, right: 50, bottom: 100, left: 150 };

    const data = visualizations.complexity_heatmap;
    
    // Create scales
    const x = d3.scaleBand()
      .domain(data.metrics)
      .range([margin.left, width - margin.right])
      .padding(0.1);

    const y = d3.scaleBand()
      .domain(data.files)
      .range([margin.top, height - margin.bottom])
      .padding(0.1);

    const color = d3.scaleSequential()
      .interpolator(d3.interpolateYlOrRd)
      .domain([0, d3.max(data.values, (d: any) => d.value) || 10]);

    // Create the heatmap cells
    svg.selectAll("rect")
      .data(data.values)
      .enter()
      .append("rect")
      .attr("x", (d: any) => x(d.metric) || 0)
      .attr("y", (d: any) => y(d.file) || 0)
      .attr("width", x.bandwidth())
      .attr("height", y.bandwidth())
      .attr("fill", (d: any) => color(d.value))
      .attr("stroke", "white")
      .attr("stroke-width", 0.5)
      .on("click", (event, d: any) => {
        if (onNodeClick && d.file) {
          onNodeClick(d.file);
        }
      })
      .append("title")
      .text((d: any) => `${d.file}\n${d.metric}: ${d.value}`);

    // Add x-axis
    svg.append("g")
      .attr("transform", `translate(0,${height - margin.bottom})`)
      .call(d3.axisBottom(x))
      .selectAll("text")
      .attr("transform", "rotate(-45)")
      .style("text-anchor", "end")
      .attr("dx", "-.8em")
      .attr("dy", ".15em");

    // Add y-axis
    svg.append("g")
      .attr("transform", `translate(${margin.left},0)`)
      .call(d3.axisLeft(y));

    // Add title
    svg.append("text")
      .attr("x", width / 2)
      .attr("y", margin.top / 2)
      .attr("text-anchor", "middle")
      .style("font-size", "16px")
      .style("fill", textColor)
      .text("Code Complexity Heatmap");
  };

  const handleVisualizationChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedVisualization(e.target.value);
  };

  if (loading) {
    return (
      <Box textAlign="center" py={10}>
        <Spinner size="xl" />
        <Text mt={4}>Loading visualizations...</Text>
      </Box>
    );
  }

  if (error) {
    return (
      <Alert status="error">
        <AlertIcon />
        {error}
      </Alert>
    );
  }

  if (!visualizations) {
    return (
      <Alert status="info">
        <AlertIcon />
        No visualization data available for this file or project.
      </Alert>
    );
  }

  return (
    <Box>
      <Heading size="lg" mb={4}>
        Code Visualizations
      </Heading>

      <HStack mb={4}>
        <Select 
          value={selectedVisualization} 
          onChange={handleVisualizationChange}
          width="300px"
        >
          <option value="dependency_graph">Dependency Graph</option>
          <option value="complexity_heatmap">Complexity Heatmap</option>
          <option value="call_graph">Call Graph</option>
          <option value="inheritance_tree">Inheritance Tree</option>
        </Select>
        
        <Button
          onClick={() => {
            if (selectedVisualization === 'dependency_graph') {
              renderDependencyGraph();
            } else if (selectedVisualization === 'complexity_heatmap') {
              renderComplexityHeatmap();
            }
          }}
        >
          Refresh
        </Button>
      </HStack>

      <Box 
        borderWidth="1px" 
        borderRadius="md" 
        p={4} 
        bg={bgColor}
        height="600px"
        overflow="hidden"
      >
        <svg 
          ref={svgRef} 
          width="100%" 
          height="100%"
          style={{ overflow: 'visible' }}
        />
      </Box>
    </Box>
  );
};

export default CodeVisualization;