import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Heading, 
  Button, 
  VStack, 
  HStack, 
  Text, 
  Card, 
  CardBody, 
  CardFooter,
  Badge,
  useDisclosure,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  ModalCloseButton,
  FormControl,
  FormLabel,
  Input,
  Select,
  Switch,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Divider,
  useToast,
  Spinner,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  Tooltip,
  IconButton,
  Flex,
  Spacer
} from '@chakra-ui/react';
import { useNavigate } from 'react-router-dom';
import { FaFolder, FaPlus, FaSearch, FaInfoCircle, FaSync, FaExternalLinkAlt } from 'react-icons/fa';
import { projectApi, systemApi } from '../services/api';
import { Project } from '../types';

interface SystemInfo {
  is_wsl: boolean;
  wsl_version: number | null;
  python_version: string;
  codegen_version: string | null;
  platform: string;
}

interface ProjectCandidate {
  name: string;
  path: string;
  language: string | null;
  indicators: string[];
}

const ProjectsPage: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [path, setPath] = useState('');
  const [language, setLanguage] = useState('');
  const [autoInit, setAutoInit] = useState(false);
  const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null);
  const [systemInfoLoading, setSystemInfoLoading] = useState(false);
  const [projectCandidates, setProjectCandidates] = useState<ProjectCandidate[]>([]);
  const [scanPath, setScanPath] = useState('');
  const [scanningProjects, setScanningProjects] = useState(false);
  const [initializingProject, setInitializingProject] = useState(false);
  const [selectedCandidate, setSelectedCandidate] = useState<ProjectCandidate | null>(null);
  
  const { isOpen, onOpen, onClose } = useDisclosure();
  const scanModalDisclosure = useDisclosure();
  const initModalDisclosure = useDisclosure();
  
  const navigate = useNavigate();
  const toast = useToast();

  useEffect(() => {
    fetchProjects();
    fetchSystemInfo();
  }, []);

  const fetchProjects = async () => {
    try {
      setLoading(true);
      const response = await projectApi.listProjects();
      setProjects(response.data);
    } catch (error) {
      console.error('Error fetching projects:', error);
      toast({
        title: 'Error fetching projects',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    } finally {
      setLoading(false);
    }
  };

  const fetchSystemInfo = async () => {
    try {
      setSystemInfoLoading(true);
      const response = await systemApi.getSystemInfo();
      setSystemInfo(response.data);
    } catch (error) {
      console.error('Error fetching system info:', error);
      toast({
        title: 'Error fetching system information',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    } finally {
      setSystemInfoLoading(false);
    }
  };

  const scanForProjects = async () => {
    try {
      setScanningProjects(true);
      const response = await systemApi.scanProjects({ base_path: scanPath || undefined });
      
      if (response.data.success) {
        setProjectCandidates(response.data.projects);
        
        if (response.data.projects.length === 0) {
          toast({
            title: 'No projects found',
            description: 'No potential projects were found in the specified location.',
            status: 'info',
            duration: 3000,
            isClosable: true,
          });
        }
      } else {
        toast({
          title: 'Error scanning for projects',
          description: response.data.message,
          status: 'error',
          duration: 3000,
          isClosable: true,
        });
      }
    } catch (error) {
      console.error('Error scanning for projects:', error);
      toast({
        title: 'Error scanning for projects',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    } finally {
      setScanningProjects(false);
    }
  };

  const initializeProject = async () => {
    if (!selectedCandidate) return;
    
    try {
      setInitializingProject(true);
      const response = await systemApi.initialize({
        path: selectedCandidate.path,
        language: selectedCandidate.language || undefined
      });
      
      if (response.data.success) {
        toast({
          title: 'Project initialized',
          description: 'Project has been successfully initialized with codegen.',
          status: 'success',
          duration: 3000,
          isClosable: true,
        });
        
        // Create the project in the UI
        handleCreateProject({
          path: selectedCandidate.path,
          language: selectedCandidate.language || undefined,
          auto_init: false // Already initialized
        });
        
        initModalDisclosure.onClose();
      } else {
        toast({
          title: 'Error initializing project',
          description: response.data.message,
          status: 'error',
          duration: 5000,
          isClosable: true,
        });
      }
    } catch (error) {
      console.error('Error initializing project:', error);
      toast({
        title: 'Error initializing project',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    } finally {
      setInitializingProject(false);
    }
  };

  const handleCreateProject = async (projectData: { path: string; language?: string; auto_init?: boolean }) => {
    try {
      const response = await projectApi.createProject(projectData);
      
      toast({
        title: 'Project created',
        description: `Project ${response.data.name} created successfully`,
        status: 'success',
        duration: 3000,
        isClosable: true,
      });
      
      setProjects([...projects, response.data]);
      onClose();
      navigate(`/projects/${response.data.id}`);
    } catch (error) {
      console.error('Error creating project:', error);
      toast({
        title: 'Error creating project',
        description: error instanceof Error ? error.message : 'Unknown error',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    }
  };

  const handleSelectCandidate = (candidate: ProjectCandidate) => {
    setSelectedCandidate(candidate);
    initModalDisclosure.onOpen();
  };

  return (
    <Box p={8}>
      <HStack mb={8} justifyContent="space-between">
        <Heading>Projects</Heading>
        <HStack>
          <Button leftIcon={<FaSearch />} colorScheme="blue" onClick={scanModalDisclosure.onOpen}>
            Discover Projects
          </Button>
          <Button leftIcon={<FaPlus />} colorScheme="brand" onClick={onOpen}>
            New Project
          </Button>
        </HStack>
      </HStack>

      {systemInfo && systemInfo.is_wsl && (
        <Alert status="info" mb={4} borderRadius="md">
          <AlertIcon />
          <Box>
            <AlertTitle>Running in WSL{systemInfo.wsl_version}</AlertTitle>
            <AlertDescription>
              Windows paths will be automatically converted to WSL paths.
            </AlertDescription>
          </Box>
        </Alert>
      )}

      {loading ? (
        <Box textAlign="center" p={8}>
          <Spinner size="xl" />
          <Text mt={4}>Loading projects...</Text>
        </Box>
      ) : projects.length === 0 ? (
        <Box textAlign="center" p={8}>
          <Text mb={4}>No projects found. Create a new project to get started.</Text>
          <HStack justifyContent="center" spacing={4}>
            <Button leftIcon={<FaSearch />} colorScheme="blue" onClick={scanModalDisclosure.onOpen}>
              Discover Projects
            </Button>
            <Button leftIcon={<FaPlus />} colorScheme="brand" onClick={onOpen}>
              Create Project
            </Button>
          </HStack>
        </Box>
      ) : (
        <VStack spacing={4} align="stretch">
          {projects.map((project) => (
            <Card key={project.id} variant="outline" cursor="pointer" onClick={() => navigate(`/projects/${project.id}`)}>
              <CardBody>
                <HStack>
                  <FaFolder size={24} color="#4299E1" />
                  <Box>
                    <Heading size="md">{project.name}</Heading>
                    <Text color="gray.500">{project.path}</Text>
                  </Box>
                </HStack>
              </CardBody>
              <CardFooter pt={0}>
                <Badge colorScheme="blue">{project.language}</Badge>
                {project.initialized && (
                  <Badge colorScheme="green" ml={2}>Initialized</Badge>
                )}
              </CardFooter>
            </Card>
          ))}
        </VStack>
      )}

      {/* Create Project Modal */}
      <Modal isOpen={isOpen} onClose={onClose} size="lg">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Create New Project</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <VStack spacing={4}>
              <FormControl isRequired>
                <FormLabel>Project Path</FormLabel>
                <Input 
                  placeholder="Enter absolute path to project directory" 
                  value={path}
                  onChange={(e) => setPath(e.target.value)}
                />
                {systemInfo && systemInfo.is_wsl && (
                  <Text fontSize="sm" color="blue.500" mt={1}>
                    Windows paths (e.g., C:\Projects\MyProject) will be automatically converted to WSL paths.
                  </Text>
                )}
              </FormControl>
              <FormControl>
                <FormLabel>Language (Optional)</FormLabel>
                <Select 
                  placeholder="Select language" 
                  value={language}
                  onChange={(e) => setLanguage(e.target.value)}
                >
                  <option value="python">Python</option>
                  <option value="typescript">TypeScript</option>
                  <option value="javascript">JavaScript</option>
                  <option value="go">Go</option>
                  <option value="rust">Rust</option>
                </Select>
              </FormControl>
              <FormControl>
                <HStack>
                  <FormLabel htmlFor="auto-init" mb="0">
                    Initialize with codegen
                  </FormLabel>
                  <Tooltip label="Run 'codegen init' on the project after creation">
                    <span><FaInfoCircle /></span>
                  </Tooltip>
                </HStack>
                <Switch 
                  id="auto-init" 
                  isChecked={autoInit}
                  onChange={(e) => setAutoInit(e.target.checked)}
                />
              </FormControl>
            </VStack>
          </ModalBody>

          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onClose}>
              Cancel
            </Button>
            <Button 
              colorScheme="brand" 
              onClick={() => handleCreateProject({ path, language: language || undefined, auto_init: autoInit })}
              isDisabled={!path}
            >
              Create
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      {/* Scan Projects Modal */}
      <Modal isOpen={scanModalDisclosure.isOpen} onClose={scanModalDisclosure.onClose} size="xl">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Discover Projects</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <VStack spacing={4} align="stretch">
              <FormControl>
                <FormLabel>Base Path (Optional)</FormLabel>
                <HStack>
                  <Input 
                    placeholder="Enter path to scan for projects" 
                    value={scanPath}
                    onChange={(e) => setScanPath(e.target.value)}
                  />
                  <Button 
                    colorScheme="blue" 
                    onClick={scanForProjects}
                    isLoading={scanningProjects}
                  >
                    Scan
                  </Button>
                </HStack>
                <Text fontSize="sm" color="gray.500" mt={1}>
                  Leave empty to scan common locations. This will search for projects with common indicators like .git, package.json, etc.
                </Text>
              </FormControl>

              <Divider my={2} />

              {scanningProjects ? (
                <Box textAlign="center" p={4}>
                  <Spinner size="lg" />
                  <Text mt={2}>Scanning for projects...</Text>
                </Box>
              ) : projectCandidates.length > 0 ? (
                <Box>
                  <Heading size="sm" mb={2}>Found Projects</Heading>
                  <VStack spacing={3} align="stretch" maxH="400px" overflowY="auto">
                    {projectCandidates.map((candidate, index) => (
                      <Card key={index} variant="outline" size="sm">
                        <CardBody py={3}>
                          <Flex align="center">
                            <Box>
                              <Heading size="sm">{candidate.name}</Heading>
                              <Text fontSize="sm" color="gray.500">{candidate.path}</Text>
                              <HStack mt={1}>
                                {candidate.language && (
                                  <Badge colorScheme="blue">{candidate.language}</Badge>
                                )}
                                {candidate.indicators.map((indicator, i) => (
                                  <Badge key={i} colorScheme="gray">{indicator}</Badge>
                                ))}
                              </HStack>
                            </Box>
                            <Spacer />
                            <Button 
                              size="sm" 
                              colorScheme="brand"
                              onClick={() => handleSelectCandidate(candidate)}
                            >
                              Select
                            </Button>
                          </Flex>
                        </CardBody>
                      </Card>
                    ))}
                  </VStack>
                </Box>
              ) : (
                <Text color="gray.500" textAlign="center" py={4}>
                  No projects found. Try scanning a different location.
                </Text>
              )}
            </VStack>
          </ModalBody>

          <ModalFooter>
            <Button onClick={scanModalDisclosure.onClose}>
              Close
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      {/* Initialize Project Modal */}
      <Modal isOpen={initModalDisclosure.isOpen} onClose={initModalDisclosure.onClose}>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Initialize Project</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            {selectedCandidate && (
              <VStack spacing={4} align="stretch">
                <Box>
                  <Heading size="sm">Project</Heading>
                  <Text>{selectedCandidate.name}</Text>
                </Box>
                <Box>
                  <Heading size="sm">Path</Heading>
                  <Text>{selectedCandidate.path}</Text>
                </Box>
                <Box>
                  <Heading size="sm">Language</Heading>
                  <Text>{selectedCandidate.language || 'Auto-detect'}</Text>
                </Box>
                <Alert status="info">
                  <AlertIcon />
                  <Box>
                    <AlertTitle>About to initialize</AlertTitle>
                    <AlertDescription>
                      This will run 'codegen init' on the project, which will analyze the codebase and prepare it for use with CodeGen.
                    </AlertDescription>
                  </Box>
                </Alert>
              </VStack>
            )}
          </ModalBody>

          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={initModalDisclosure.onClose}>
              Cancel
            </Button>
            <Button 
              colorScheme="brand" 
              onClick={initializeProject}
              isLoading={initializingProject}
            >
              Initialize
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Box>
  );
};

export default ProjectsPage;