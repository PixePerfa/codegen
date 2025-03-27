import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Heading, 
  Spinner, 
  Text,
  SimpleGrid,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  Button,
  useToast,
  Divider
} from '@chakra-ui/react';
import { analysisApi } from '../services/api';
import { CodeMetrics as CodeMetricsType } from '../types';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

interface CodeMetricsProps {
  projectId: string;
}

const CodeMetrics: React.FC<CodeMetricsProps> = ({ projectId }) => {
  const [metrics, setMetrics] = useState<CodeMetricsType | null>(null);
  const [loading, setLoading] = useState(true);
  const [complexity, setComplexity] = useState<any[]>([]);
  const toast = useToast();

  useEffect(() => {
    fetchMetrics();
  }, [projectId]);

  const fetchMetrics = async () => {
    try {
      setLoading(true);
      
      // Fetch basic metrics
      const metricsResponse = await analysisApi.analyze(projectId, {
        type: 'metrics'
      });
      
      setMetrics(metricsResponse.data.result);
      
      // Fetch complexity metrics
      const complexityResponse = await analysisApi.analyze(projectId, {
        type: 'complexity'
      });
      
      // Process complexity data for chart
      const complexityData = Object.entries(complexityResponse.data.result || {})
        .map(([name, value]: [string, any]) => ({
          name: name.length > 20 ? name.substring(0, 20) + '...' : name,
          fullName: name,
          complexity: value.complexity || 0,
          lines: value.lines || 0
        }))
        .sort((a, b) => b.complexity - a.complexity)
        .slice(0, 10); // Top 10 most complex functions/methods
      
      setComplexity(complexityData);
    } catch (error) {
      console.error('Error fetching metrics:', error);
      toast({
        title: 'Error fetching metrics',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Box textAlign="center" py={8}>
        <Spinner />
        <Text mt={2}>Loading code metrics...</Text>
      </Box>
    );
  }

  if (!metrics) {
    return (
      <Box textAlign="center" py={8}>
        <Text>No metrics available</Text>
        <Button mt={4} onClick={fetchMetrics}>Refresh</Button>
      </Box>
    );
  }

  return (
    <Box h="100%" display="flex" flexDirection="column" p={4}>
      <Heading size="md" mb={4}>Code Metrics</Heading>
      
      <SimpleGrid columns={{ base: 2, md: 4 }} spacing={6} mb={6}>
        <Stat>
          <StatLabel>Total Files</StatLabel>
          <StatNumber>{metrics.total_files}</StatNumber>
          <StatHelpText>Source files in codebase</StatHelpText>
        </Stat>
        
        <Stat>
          <StatLabel>Total Symbols</StatLabel>
          <StatNumber>{metrics.total_symbols}</StatNumber>
          <StatHelpText>Classes, functions, etc.</StatHelpText>
        </Stat>
        
        <Stat>
          <StatLabel>Classes</StatLabel>
          <StatNumber>{metrics.total_classes}</StatNumber>
          <StatHelpText>{((metrics.total_classes / metrics.total_symbols) * 100).toFixed(1)}% of symbols</StatHelpText>
        </Stat>
        
        <Stat>
          <StatLabel>Functions</StatLabel>
          <StatNumber>{metrics.total_functions}</StatNumber>
          <StatHelpText>{((metrics.total_functions / metrics.total_symbols) * 100).toFixed(1)}% of symbols</StatHelpText>
        </Stat>
      </SimpleGrid>
      
      <Stat mb={6}>
        <StatLabel>Lines of Code</StatLabel>
        <StatNumber>{metrics.lines_of_code.toLocaleString()}</StatNumber>
        <StatHelpText>Average {(metrics.lines_of_code / metrics.total_files).toFixed(1)} lines per file</StatHelpText>
      </Stat>
      
      <Divider mb={6} />
      
      <Heading size="md" mb={4}>Complexity Analysis</Heading>
      
      {complexity.length > 0 ? (
        <Box flex="1" minH="300px">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={complexity}>
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip 
                formatter={(value, name, props) => [value, 'Complexity']}
                labelFormatter={(label) => {
                  const item = complexity.find(c => c.name === label);
                  return item ? item.fullName : label;
                }}
              />
              <Bar dataKey="complexity" fill="#8884d8" />
            </BarChart>
          </ResponsiveContainer>
          <Text fontSize="sm" textAlign="center" mt={2}>
            Top 10 most complex functions/methods
          </Text>
        </Box>
      ) : (
        <Box textAlign="center" py={8}>
          <Text>No complexity data available</Text>
        </Box>
      )}
      
      <Button mt={4} onClick={fetchMetrics} alignSelf="flex-end">
        Refresh Metrics
      </Button>
    </Box>
  );
};

export default CodeMetrics;