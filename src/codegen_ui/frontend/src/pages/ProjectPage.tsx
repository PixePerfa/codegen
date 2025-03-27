import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Grid, 
  GridItem, 
  Tabs, 
  TabList, 
  TabPanels, 
  Tab, 
  TabPanel,
  Heading,
  Text,
  Flex,
  Badge,
  Spinner,
  useToast,
  HStack
} from '@chakra-ui/react';
import { useParams, useNavigate } from 'react-router-dom';
import { projectApi } from '../services/api';
import { Project, File } from '../types';
import FileExplorer from '../components/FileExplorer';
import CodeEditor from '../components/CodeEditor';
import SymbolBrowser from '../components/SymbolBrowser';
import CodeSearch from '../components/CodeSearch';
import CodeTransform from '../components/CodeTransform';
import DependencyGraph from '../components/DependencyGraph';
import CodeMetrics from '../components/CodeMetrics';
import BatchOperations from '../components/BatchOperations';
import GitOperations from '../components/GitOperations';
import CodeQualityAnalysis from '../components/CodeQualityAnalysis';
import AdvancedCodeAnalysis from '../components/AdvancedCodeAnalysis';
import CodeVisualization from '../components/CodeVisualization';
import CodebaseOperations from '../components/CodebaseOperations';
import SymbolUsages from '../components/SymbolUsages';
import RegexSearch from '../components/RegexSearch';
import CreateDirectory from '../components/CreateDirectory';

const ProjectPage: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const navigate = useNavigate();
  const toast = useToast();

  useEffect(() => {
    if (!projectId) {
      navigate('/');
      return;
    }
    
    fetchProject();
  }, [projectId]);

  const fetchProject = async () => {
    try {
      setLoading(true);
      const response = await projectApi.getProject(projectId);
      setProject(response.data);
    } catch (error) {
      console.error('Error fetching project:', error);
      toast({
        title: 'Error fetching project',
        description: 'Could not load project details',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
      navigate('/');
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelect = (file: File) => {
    setSelectedFile(file);
  };

  const handleRefresh = () => {
    fetchProject();
  };

  const handleApplyRefactoring = async (filePath: string, content: string) => {
    try {
      await projectApi.fileApi.updateFile(projectId, filePath, { path: filePath, content });
      toast({
        title: 'Refactoring applied',
        description: `Changes applied to ${filePath}`,
        status: 'success',
        duration: 3000,
        isClosable: true,
      });
      handleRefresh();
    } catch (error) {
      console.error('Error applying refactoring:', error);
      toast({
        title: 'Error applying refactoring',
        description: 'Could not apply changes',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    }
  };

  const handleFileClick = (filePath: string, line?: number) => {
    try {
      projectApi.fileApi.getFile(projectId, filePath)
        .then(response => {
          handleFileSelect(response.data);
          // TODO: Scroll to line in editor
        })
        .catch(error => {
          console.error('Error loading file:', error);
          toast({
            title: 'Error loading file',
            description: `Could not load file: ${filePath}`,
            status: 'error',
            duration: 3000,
            isClosable: true,
          });
        });
    } catch (error) {
      console.error('Error handling file click:', error);
    }
  };

  if (loading) {
    return (
      <Flex height="100%" alignItems="center" justifyContent="center">
        <Box textAlign="center">
          <Spinner size="xl" mb={4} />
          <Text>Loading project...</Text>
        </Box>
      </Flex>
    );
  }

  if (!project) {
    return (
      <Flex height="100%" alignItems="center" justifyContent="center">
        <Text>Project not found</Text>
      </Flex>
    );
  }

  return (
    <Box p={4} h="calc(100vh - 60px)">
      <Flex mb={4} alignItems="center" justifyContent="space-between">
        <Box>
          <Heading size="lg">{project.name}</Heading>
          <Text color="gray.500">{project.path}</Text>
        </Box>
        <HStack spacing={4}>
          <Badge colorScheme="blue">{project.language}</Badge>
          <CreateDirectory 
            projectId={projectId} 
            onDirectoryCreated={handleRefresh} 
          />
        </HStack>
      </Flex>
      
      <Grid
        h="calc(100% - 60px)"
        templateRows="auto 1fr"
        templateColumns="300px 1fr"
        gap={4}
      >
        <GridItem rowSpan={1} colSpan={2}>
          <CodebaseOperations projectId={projectId} />
        </GridItem>
        
        <GridItem rowSpan={1} colSpan={1} borderWidth="1px" borderRadius="md" overflow="hidden">
          <Tabs isFitted variant="enclosed" h="100%" display="flex" flexDirection="column">
            <TabList>
              <Tab>Files</Tab>
              <Tab>Symbols</Tab>
              <Tab>Search</Tab>
              <Tab>Transform</Tab>
              <Tab>Analysis</Tab>
              <Tab>Advanced</Tab>
              <Tab>Batch</Tab>
              <Tab>Git</Tab>
            </TabList>
            
            <TabPanels flex="1" overflow="hidden">
              <TabPanel p={4} h="100%" overflow="auto">
                <FileExplorer 
                  projectId={projectId} 
                  onFileSelect={handleFileSelect} 
                />
              </TabPanel>
              <TabPanel p={0} h="100%" overflow="auto">
                <Tabs variant="soft-rounded" colorScheme="blue" h="100%" display="flex" flexDirection="column">
                  <TabList px={4} pt={4}>
                    <Tab>Browser</Tab>
                    <Tab>Usages</Tab>
                  </TabList>
                  <TabPanels flex="1" overflow="auto">
                    <TabPanel p={4} h="100%" overflow="auto">
                      <SymbolBrowser 
                        projectId={projectId} 
                        onSymbolSelect={handleFileSelect} 
                      />
                    </TabPanel>
                    <TabPanel p={4} h="100%" overflow="auto">
                      <SymbolUsages 
                        projectId={projectId} 
                        onFileClick={handleFileClick} 
                      />
                    </TabPanel>
                  </TabPanels>
                </Tabs>
              </TabPanel>
              <TabPanel p={0} h="100%" overflow="auto">
                <Tabs variant="soft-rounded" colorScheme="blue" h="100%" display="flex" flexDirection="column">
                  <TabList px={4} pt={4}>
                    <Tab>Text</Tab>
                    <Tab>Regex</Tab>
                  </TabList>
                  <TabPanels flex="1" overflow="auto">
                    <TabPanel p={4} h="100%" overflow="auto">
                      <CodeSearch 
                        projectId={projectId} 
                        onResultSelect={handleFileSelect} 
                      />
                    </TabPanel>
                    <TabPanel p={4} h="100%" overflow="auto">
                      <RegexSearch 
                        projectId={projectId} 
                        onFileClick={handleFileClick} 
                      />
                    </TabPanel>
                  </TabPanels>
                </Tabs>
              </TabPanel>
              <TabPanel p={4} h="100%" overflow="auto">
                <CodeTransform 
                  projectId={projectId} 
                  onTransformComplete={handleRefresh} 
                />
              </TabPanel>
              <TabPanel p={0} h="100%" overflow="auto">
                <Tabs variant="soft-rounded" colorScheme="blue" h="100%" display="flex" flexDirection="column">
                  <TabList px={4} pt={4}>
                    <Tab>Dependencies</Tab>
                    <Tab>Metrics</Tab>
                    <Tab>Quality</Tab>
                    <Tab>Visualizations</Tab>
                  </TabList>
                  <TabPanels flex="1" overflow="auto">
                    <TabPanel p={4} h="100%" overflow="auto">
                      <DependencyGraph 
                        projectId={projectId} 
                        onNodeClick={handleFileSelect} 
                      />
                    </TabPanel>
                    <TabPanel p={4} h="100%" overflow="auto">
                      <CodeMetrics 
                        projectId={projectId} 
                      />
                    </TabPanel>
                    <TabPanel p={4} h="100%" overflow="auto">
                      <CodeQualityAnalysis 
                        projectId={projectId}
                        filePath={selectedFile?.path}
                      />
                    </TabPanel>
                    <TabPanel p={4} h="100%" overflow="auto">
                      <CodeVisualization 
                        projectId={projectId}
                        filePath={selectedFile?.path}
                        onNodeClick={handleFileClick}
                      />
                    </TabPanel>
                  </TabPanels>
                </Tabs>
              </TabPanel>
              <TabPanel p={4} h="100%" overflow="auto">
                <AdvancedCodeAnalysis 
                  projectId={projectId}
                  filePath={selectedFile?.path}
                  onApplyRefactoring={handleApplyRefactoring}
                />
              </TabPanel>
              <TabPanel p={4} h="100%" overflow="auto">
                <BatchOperations 
                  projectId={projectId} 
                  onOperationComplete={handleRefresh} 
                />
              </TabPanel>
              <TabPanel p={4} h="100%" overflow="auto">
                <GitOperations 
                  projectId={projectId} 
                  onOperationComplete={handleRefresh} 
                />
              </TabPanel>
            </TabPanels>
          </Tabs>
        </GridItem>
        
        <GridItem rowSpan={1} colSpan={1} borderWidth="1px" borderRadius="md" overflow="hidden">
          <CodeEditor 
            file={selectedFile} 
            projectId={projectId} 
            onSave={handleRefresh} 
          />
        </GridItem>
      </Grid>
    </Box>
  );
};

export default ProjectPage;