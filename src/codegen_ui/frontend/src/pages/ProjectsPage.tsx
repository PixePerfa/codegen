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
  useToast
} from '@chakra-ui/react';
import { useNavigate } from 'react-router-dom';
import { FaFolder, FaPlus } from 'react-icons/fa';
import { projectApi } from '../services/api';
import { Project } from '../types';

const ProjectsPage: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [path, setPath] = useState('');
  const [language, setLanguage] = useState('');
  const { isOpen, onOpen, onClose } = useDisclosure();
  const navigate = useNavigate();
  const toast = useToast();

  useEffect(() => {
    fetchProjects();
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

  const handleCreateProject = async () => {
    try {
      const response = await projectApi.createProject({
        path,
        language: language || undefined,
      });
      
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

  return (
    <Box p={8}>
      <HStack mb={8} justifyContent="space-between">
        <Heading>Projects</Heading>
        <Button leftIcon={<FaPlus />} colorScheme="brand" onClick={onOpen}>
          New Project
        </Button>
      </HStack>

      {loading ? (
        <Text>Loading projects...</Text>
      ) : projects.length === 0 ? (
        <Box textAlign="center" p={8}>
          <Text mb={4}>No projects found. Create a new project to get started.</Text>
          <Button leftIcon={<FaPlus />} colorScheme="brand" onClick={onOpen}>
            Create Project
          </Button>
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
              </CardFooter>
            </Card>
          ))}
        </VStack>
      )}

      {/* Create Project Modal */}
      <Modal isOpen={isOpen} onClose={onClose}>
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
                </Select>
              </FormControl>
            </VStack>
          </ModalBody>

          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onClose}>
              Cancel
            </Button>
            <Button 
              colorScheme="brand" 
              onClick={handleCreateProject}
              isDisabled={!path}
            >
              Create
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Box>
  );
};

export default ProjectsPage;