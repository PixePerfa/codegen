import React, { useState, useEffect } from 'react';
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
  Button,
  VStack,
  HStack,
  Badge,
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon,
  useToast,
  Code,
  Divider,
} from '@chakra-ui/react';
import { projectApi } from '../services/api';

interface AdvancedCodeAnalysisProps {
  projectId: string;
  filePath?: string;
  onApplyRefactoring?: (filePath: string, content: string) => void;
}

const AdvancedCodeAnalysis: React.FC<AdvancedCodeAnalysisProps> = ({ 
  projectId, 
  filePath,
  onApplyRefactoring 
}) => {
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [codeQuality, setCodeQuality] = useState<any>(null);
  const [refactoringSuggestions, setRefactoringSuggestions] = useState<any>(null);
  const [testSuggestions, setTestSuggestions] = useState<any>(null);
  const [documentation, setDocumentation] = useState<any>(null);
  const toast = useToast();

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        
        // Load all data in parallel
        const [
          codeQualityResponse,
          refactoringResponse,
          testResponse,
          documentationResponse
        ] = await Promise.all([
          projectApi.getCodeQuality(projectId, filePath),
          projectApi.getRefactoringSuggestions(projectId, filePath),
          projectApi.getTestGeneration(projectId, filePath),
          projectApi.getDocumentation(projectId, filePath)
        ]);
        
        setCodeQuality(codeQualityResponse.data.result);
        setRefactoringSuggestions(refactoringResponse.data.result);
        setTestSuggestions(testResponse.data.result);
        setDocumentation(documentationResponse.data.result);
        setError(null);
      } catch (err) {
        setError('Failed to load advanced code analysis');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [projectId, filePath]);

  const handleApplyRefactoring = (filePath: string, newContent: string) => {
    if (onApplyRefactoring) {
      onApplyRefactoring(filePath, newContent);
      toast({
        title: "Refactoring applied",
        description: `Changes applied to ${filePath}`,
        status: "success",
        duration: 3000,
        isClosable: true,
      });
    }
  };

  if (loading) {
    return (
      <Box textAlign="center" py={10}>
        <Spinner size="xl" />
        <Text mt={4}>Loading advanced code analysis...</Text>
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

  return (
    <Box>
      <Heading size="lg" mb={4}>
        Advanced Code Analysis
      </Heading>

      <Tabs variant="enclosed">
        <TabList>
          <Tab>Refactoring Suggestions</Tab>
          <Tab>Test Generation</Tab>
          <Tab>Documentation</Tab>
        </TabList>

        <TabPanels>
          <TabPanel>
            <Box>
              <Heading size="md" mb={4}>
                Refactoring Suggestions
              </Heading>
              
              {refactoringSuggestions && Object.keys(refactoringSuggestions).length > 0 ? (
                <Accordion allowMultiple>
                  {Object.entries(refactoringSuggestions).map(([filePath, suggestions]: [string, any]) => (
                    <AccordionItem key={filePath}>
                      <h2>
                        <AccordionButton>
                          <Box flex="1" textAlign="left">
                            {filePath}
                          </Box>
                          <Badge colorScheme="blue" mr={2}>
                            {suggestions.length} suggestions
                          </Badge>
                          <AccordionIcon />
                        </AccordionButton>
                      </h2>
                      <AccordionPanel pb={4}>
                        <VStack align="stretch" spacing={4}>
                          {suggestions.map((suggestion: any, index: number) => (
                            <Box 
                              key={index} 
                              p={4} 
                              borderWidth="1px" 
                              borderRadius="md"
                              borderColor="blue.200"
                              bg="blue.50"
                            >
                              <Heading size="sm" mb={2}>
                                {suggestion.title}
                              </Heading>
                              <Text mb={2}>{suggestion.description}</Text>
                              
                              <Divider my={2} />
                              
                              <Heading size="xs" mb={2}>
                                Current Code:
                              </Heading>
                              <Code p={2} mb={3} display="block" whiteSpace="pre" overflowX="auto">
                                {suggestion.original_code}
                              </Code>
                              
                              <Heading size="xs" mb={2}>
                                Suggested Code:
                              </Heading>
                              <Code p={2} mb={3} display="block" whiteSpace="pre" overflowX="auto" bg="green.50">
                                {suggestion.refactored_code}
                              </Code>
                              
                              <Button 
                                colorScheme="blue" 
                                size="sm"
                                onClick={() => handleApplyRefactoring(filePath, suggestion.refactored_code)}
                              >
                                Apply Refactoring
                              </Button>
                            </Box>
                          ))}
                        </VStack>
                      </AccordionPanel>
                    </AccordionItem>
                  ))}
                </Accordion>
              ) : (
                <Alert status="info">
                  <AlertIcon />
                  No refactoring suggestions available for this file or project.
                </Alert>
              )}
            </Box>
          </TabPanel>

          <TabPanel>
            <Box>
              <Heading size="md" mb={4}>
                Test Generation
              </Heading>
              
              {testSuggestions && Object.keys(testSuggestions).length > 0 ? (
                <Accordion allowMultiple>
                  {Object.entries(testSuggestions).map(([filePath, tests]: [string, any]) => (
                    <AccordionItem key={filePath}>
                      <h2>
                        <AccordionButton>
                          <Box flex="1" textAlign="left">
                            {filePath}
                          </Box>
                          <Badge colorScheme="purple" mr={2}>
                            {tests.length} tests
                          </Badge>
                          <AccordionIcon />
                        </AccordionButton>
                      </h2>
                      <AccordionPanel pb={4}>
                        <VStack align="stretch" spacing={4}>
                          {tests.map((test: any, index: number) => (
                            <Box 
                              key={index} 
                              p={4} 
                              borderWidth="1px" 
                              borderRadius="md"
                              borderColor="purple.200"
                              bg="purple.50"
                            >
                              <Heading size="sm" mb={2}>
                                Test for: {test.function_name}
                              </Heading>
                              
                              <Code p={2} display="block" whiteSpace="pre" overflowX="auto">
                                {test.test_code}
                              </Code>
                              
                              <HStack mt={3}>
                                <Button 
                                  colorScheme="purple" 
                                  size="sm"
                                  onClick={() => {
                                    // Copy to clipboard
                                    navigator.clipboard.writeText(test.test_code);
                                    toast({
                                      title: "Copied to clipboard",
                                      status: "success",
                                      duration: 2000,
                                    });
                                  }}
                                >
                                  Copy to Clipboard
                                </Button>
                                
                                <Button 
                                  colorScheme="purple" 
                                  size="sm"
                                  variant="outline"
                                  onClick={() => {
                                    // Create test file
                                    const testFilePath = filePath.replace('.py', '_test.py');
                                    handleApplyRefactoring(testFilePath, test.test_code);
                                  }}
                                >
                                  Create Test File
                                </Button>
                              </HStack>
                            </Box>
                          ))}
                        </VStack>
                      </AccordionPanel>
                    </AccordionItem>
                  ))}
                </Accordion>
              ) : (
                <Alert status="info">
                  <AlertIcon />
                  No test suggestions available for this file or project.
                </Alert>
              )}
            </Box>
          </TabPanel>

          <TabPanel>
            <Box>
              <Heading size="md" mb={4}>
                Documentation Analysis
              </Heading>
              
              {documentation && Object.keys(documentation).length > 0 ? (
                <Accordion allowMultiple>
                  {Object.entries(documentation).map(([filePath, docs]: [string, any]) => (
                    <AccordionItem key={filePath}>
                      <h2>
                        <AccordionButton>
                          <Box flex="1" textAlign="left">
                            {filePath}
                          </Box>
                          <Badge colorScheme="green" mr={2}>
                            {docs.coverage ? `${Math.round(docs.coverage * 100)}% coverage` : 'N/A'}
                          </Badge>
                          <AccordionIcon />
                        </AccordionButton>
                      </h2>
                      <AccordionPanel pb={4}>
                        <VStack align="stretch" spacing={4}>
                          <Box mb={4}>
                            <Heading size="sm" mb={2}>
                              Documentation Coverage
                            </Heading>
                            <Text>
                              {docs.coverage 
                                ? `${Math.round(docs.coverage * 100)}% of functions and classes are documented` 
                                : 'No documentation coverage data available'}
                            </Text>
                          </Box>
                          
                          {docs.missing_docs && docs.missing_docs.length > 0 && (
                            <Box mb={4}>
                              <Heading size="sm" mb={2}>
                                Missing Documentation
                              </Heading>
                              <VStack align="stretch">
                                {docs.missing_docs.map((item: any, index: number) => (
                                  <Box 
                                    key={index} 
                                    p={3} 
                                    borderWidth="1px" 
                                    borderRadius="md"
                                    borderColor="orange.200"
                                    bg="orange.50"
                                  >
                                    <Text fontWeight="bold">{item.name}</Text>
                                    <Text fontSize="sm">Line: {item.line}</Text>
                                    <Text fontSize="sm">Type: {item.type}</Text>
                                    
                                    {item.suggested_doc && (
                                      <>
                                        <Divider my={2} />
                                        <Heading size="xs" mb={1}>
                                          Suggested Documentation:
                                        </Heading>
                                        <Code p={2} display="block" whiteSpace="pre" overflowX="auto">
                                          {item.suggested_doc}
                                        </Code>
                                        <Button 
                                          mt={2}
                                          colorScheme="green" 
                                          size="sm"
                                          onClick={() => {
                                            // Apply documentation
                                            // This would require more complex logic to insert at the right position
                                            toast({
                                              title: "Feature not implemented",
                                              description: "Adding documentation requires more complex code manipulation",
                                              status: "info",
                                              duration: 3000,
                                            });
                                          }}
                                        >
                                          Add Documentation
                                        </Button>
                                      </>
                                    )}
                                  </Box>
                                ))}
                              </VStack>
                            </Box>
                          )}
                          
                          {docs.quality_issues && docs.quality_issues.length > 0 && (
                            <Box>
                              <Heading size="sm" mb={2}>
                                Documentation Quality Issues
                              </Heading>
                              <VStack align="stretch">
                                {docs.quality_issues.map((issue: any, index: number) => (
                                  <Box 
                                    key={index} 
                                    p={3} 
                                    borderWidth="1px" 
                                    borderRadius="md"
                                    borderColor="red.200"
                                    bg="red.50"
                                  >
                                    <Text fontWeight="bold">{issue.name}</Text>
                                    <Text fontSize="sm">Line: {issue.line}</Text>
                                    <Text fontSize="sm">Issue: {issue.issue}</Text>
                                    
                                    {issue.suggestion && (
                                      <>
                                        <Divider my={2} />
                                        <Heading size="xs" mb={1}>
                                          Suggested Improvement:
                                        </Heading>
                                        <Text fontSize="sm">{issue.suggestion}</Text>
                                      </>
                                    )}
                                  </Box>
                                ))}
                              </VStack>
                            </Box>
                          )}
                        </VStack>
                      </AccordionPanel>
                    </AccordionItem>
                  ))}
                </Accordion>
              ) : (
                <Alert status="info">
                  <AlertIcon />
                  No documentation analysis available for this file or project.
                </Alert>
              )}
            </Box>
          </TabPanel>
        </TabPanels>
      </Tabs>
    </Box>
  );
};

export default AdvancedCodeAnalysis;