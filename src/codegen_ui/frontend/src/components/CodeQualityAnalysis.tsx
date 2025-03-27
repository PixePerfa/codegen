import React, { useState, useEffect } from 'react';
import {
  Box,
  Heading,
  Text,
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon,
  Badge,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Spinner,
  Alert,
  AlertIcon,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Button,
  Link,
} from '@chakra-ui/react';
import { fetchCodeQuality } from '../services/api';

interface CodeQualityAnalysisProps {
  projectId: string;
  filePath?: string;
}

const CodeQualityAnalysis: React.FC<CodeQualityAnalysisProps> = ({ projectId, filePath }) => {
  const [codeQuality, setCodeQuality] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadCodeQuality = async () => {
      try {
        setLoading(true);
        const response = await fetchCodeQuality(projectId, filePath);
        setCodeQuality(response.result);
        setError(null);
      } catch (err) {
        setError('Failed to load code quality analysis');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    loadCodeQuality();
  }, [projectId, filePath]);

  if (loading) {
    return (
      <Box textAlign="center" py={10}>
        <Spinner size="xl" />
        <Text mt={4}>Loading code quality analysis...</Text>
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

  if (!codeQuality || Object.keys(codeQuality).length === 0) {
    return (
      <Alert status="info">
        <AlertIcon />
        No code quality data available for this file or project.
      </Alert>
    );
  }

  const getComplexityColor = (complexity: number) => {
    if (complexity <= 5) return 'green';
    if (complexity <= 10) return 'yellow';
    if (complexity <= 15) return 'orange';
    return 'red';
  };

  const getMaintainabilityColor = (rating: string) => {
    switch (rating) {
      case 'A': return 'green';
      case 'B': return 'teal';
      case 'C': return 'yellow';
      case 'D': return 'orange';
      case 'F': return 'red';
      default: return 'gray';
    }
  };

  return (
    <Box>
      <Heading size="lg" mb={4}>
        Code Quality Analysis
      </Heading>

      <Accordion allowMultiple defaultIndex={[0]}>
        {Object.entries(codeQuality).map(([filePath, fileData]: [string, any]) => (
          <AccordionItem key={filePath}>
            <h2>
              <AccordionButton>
                <Box flex="1" textAlign="left">
                  {filePath}
                </Box>
                <Badge colorScheme={getMaintainabilityColor(fileData.maintainability?.rating || 'C')} mr={2}>
                  {fileData.maintainability?.rating || 'N/A'}
                </Badge>
                <AccordionIcon />
              </AccordionButton>
            </h2>
            <AccordionPanel pb={4}>
              <Tabs variant="enclosed">
                <TabList>
                  <Tab>Complexity</Tab>
                  <Tab>Issues</Tab>
                  <Tab>Style Violations</Tab>
                </TabList>

                <TabPanels>
                  <TabPanel>
                    <Box mb={4}>
                      <Heading size="sm" mb={2}>
                        Maintainability
                      </Heading>
                      <Text>
                        Maintainability Index:{' '}
                        <Badge colorScheme={getMaintainabilityColor(fileData.maintainability?.rating || 'C')}>
                          {fileData.maintainability?.maintainability_index?.toFixed(2) || 'N/A'}
                        </Badge>
                        {' '}
                        (Rating: {fileData.maintainability?.rating || 'N/A'})
                      </Text>
                    </Box>

                    <Box mb={4}>
                      <Heading size="sm" mb={2}>
                        File Metrics
                      </Heading>
                      <Text>Lines of Code: {fileData.complexity?.lines_of_code || 'N/A'}</Text>
                      <Text>Comment Ratio: {(fileData.complexity?.comment_ratio * 100).toFixed(2) || 'N/A'}%</Text>
                    </Box>

                    <Box>
                      <Heading size="sm" mb={2}>
                        Function Complexity
                      </Heading>
                      <Table variant="simple" size="sm">
                        <Thead>
                          <Tr>
                            <Th>Function</Th>
                            <Th isNumeric>Cyclomatic Complexity</Th>
                            <Th isNumeric>Cognitive Complexity</Th>
                          </Tr>
                        </Thead>
                        <Tbody>
                          {fileData.complexity?.cyclomatic_complexity &&
                            Object.entries(fileData.complexity.cyclomatic_complexity).map(
                              ([funcName, complexity]: [string, any]) => (
                                <Tr key={funcName}>
                                  <Td>{funcName}</Td>
                                  <Td isNumeric>
                                    <Badge colorScheme={getComplexityColor(complexity as number)}>
                                      {complexity}
                                    </Badge>
                                  </Td>
                                  <Td isNumeric>
                                    <Badge
                                      colorScheme={getComplexityColor(
                                        fileData.complexity.cognitive_complexity[funcName] as number
                                      )}
                                    >
                                      {fileData.complexity.cognitive_complexity[funcName]}
                                    </Badge>
                                  </Td>
                                </Tr>
                              )
                            )}
                        </Tbody>
                      </Table>
                    </Box>
                  </TabPanel>

                  <TabPanel>
                    <Box>
                      <Heading size="sm" mb={2}>
                        Code Issues
                      </Heading>
                      {fileData.issues && fileData.issues.length > 0 ? (
                        <Table variant="simple" size="sm">
                          <Thead>
                            <Tr>
                              <Th>Type</Th>
                              <Th>Location</Th>
                              <Th>Message</Th>
                            </Tr>
                          </Thead>
                          <Tbody>
                            {fileData.issues.map((issue: any, index: number) => (
                              <Tr key={index}>
                                <Td>
                                  <Badge colorScheme="red">{issue.type}</Badge>
                                </Td>
                                <Td>
                                  {issue.symbol ? `${issue.symbol} (line ${issue.line})` : `Line ${issue.line}`}
                                </Td>
                                <Td>{issue.message}</Td>
                              </Tr>
                            ))}
                          </Tbody>
                        </Table>
                      ) : (
                        <Text>No issues found.</Text>
                      )}
                    </Box>
                  </TabPanel>

                  <TabPanel>
                    <Box>
                      <Heading size="sm" mb={2}>
                        Style Violations
                      </Heading>
                      {fileData.style_violations && fileData.style_violations.length > 0 ? (
                        <Table variant="simple" size="sm">
                          <Thead>
                            <Tr>
                              <Th>Type</Th>
                              <Th>Location</Th>
                              <Th>Message</Th>
                            </Tr>
                          </Thead>
                          <Tbody>
                            {fileData.style_violations.map((violation: any, index: number) => (
                              <Tr key={index}>
                                <Td>
                                  <Badge colorScheme="purple">{violation.type}</Badge>
                                </Td>
                                <Td>
                                  {violation.symbol
                                    ? `${violation.symbol} (line ${violation.line})`
                                    : `Line ${violation.line}`}
                                </Td>
                                <Td>{violation.message}</Td>
                              </Tr>
                            ))}
                          </Tbody>
                        </Table>
                      ) : (
                        <Text>No style violations found.</Text>
                      )}
                    </Box>
                  </TabPanel>
                </TabPanels>
              </Tabs>
            </AccordionPanel>
          </AccordionItem>
        ))}
      </Accordion>
    </Box>
  );
};

export default CodeQualityAnalysis;