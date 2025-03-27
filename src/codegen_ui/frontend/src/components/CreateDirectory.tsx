import React, { useState } from 'react';
import {
  Box,
  Button,
  Flex,
  Heading,
  Input,
  Text,
  useToast,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  ModalCloseButton,
  FormControl,
  FormLabel,
  FormHelperText,
  useDisclosure,
} from '@chakra-ui/react';
import { FiFolderPlus } from 'react-icons/fi';
import { useApi } from '../services/api';

interface CreateDirectoryProps {
  projectId: string;
  onDirectoryCreated?: () => void;
}

const CreateDirectory: React.FC<CreateDirectoryProps> = ({ projectId, onDirectoryCreated }) => {
  const toast = useToast();
  const api = useApi();
  const { isOpen, onOpen, onClose } = useDisclosure();
  const [directoryPath, setDirectoryPath] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleCreateDirectory = async () => {
    if (!directoryPath.trim()) {
      toast({
        title: 'Directory path required',
        description: 'Please enter a directory path',
        status: 'warning',
        duration: 3000,
        isClosable: true,
      });
      return;
    }

    setIsLoading(true);
    try {
      const response = await api.post(`/projects/${projectId}/directories`, {
        path: directoryPath,
      });
      
      if (response.status === 'success') {
        toast({
          title: 'Directory created',
          description: response.message,
          status: 'success',
          duration: 3000,
          isClosable: true,
        });
        
        // Reset form and close modal
        setDirectoryPath('');
        onClose();
        
        // Notify parent component
        if (onDirectoryCreated) {
          onDirectoryCreated();
        }
      } else {
        throw new Error(response.message || 'Failed to create directory');
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to create directory',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      <Button
        leftIcon={<FiFolderPlus />}
        colorScheme="teal"
        onClick={onOpen}
        size="sm"
      >
        New Directory
      </Button>

      <Modal isOpen={isOpen} onClose={onClose}>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Create New Directory</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <FormControl>
              <FormLabel>Directory Path</FormLabel>
              <Input
                placeholder="Enter directory path (e.g., 'src/components', 'tests/unit')"
                value={directoryPath}
                onChange={(e) => setDirectoryPath(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleCreateDirectory()}
              />
              <FormHelperText>
                Specify the path relative to the project root. Nested directories will be created automatically.
              </FormHelperText>
            </FormControl>
          </ModalBody>

          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onClose}>
              Cancel
            </Button>
            <Button
              colorScheme="teal"
              onClick={handleCreateDirectory}
              isLoading={isLoading}
              loadingText="Creating..."
            >
              Create Directory
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </>
  );
};

export default CreateDirectory;