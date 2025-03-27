import React, { useState } from 'react';
import {
  Box,
  Button,
  Flex,
  Heading,
  Text,
  useToast,
  AlertDialog,
  AlertDialogBody,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogContent,
  AlertDialogOverlay,
} from '@chakra-ui/react';
import { FiSave, FiRefreshCw } from 'react-icons/fi';
import { useApi } from '../services/api';

interface CodebaseOperationsProps {
  projectId: string;
}

const CodebaseOperations: React.FC<CodebaseOperationsProps> = ({ projectId }) => {
  const toast = useToast();
  const api = useApi();
  const [isLoading, setIsLoading] = useState(false);
  const [isResetDialogOpen, setIsResetDialogOpen] = useState(false);
  const cancelRef = React.useRef<HTMLButtonElement>(null);

  const handleCommit = async () => {
    setIsLoading(true);
    try {
      const response = await api.post(`/projects/${projectId}/commit`);
      if (response.status === 'success') {
        toast({
          title: 'Changes committed',
          description: response.message,
          status: 'success',
          duration: 3000,
          isClosable: true,
        });
      } else {
        throw new Error(response.message || 'Failed to commit changes');
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to commit changes',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = async () => {
    setIsLoading(true);
    try {
      const response = await api.post(`/projects/${projectId}/reset`);
      if (response.status === 'success') {
        toast({
          title: 'Codebase reset',
          description: response.message,
          status: 'success',
          duration: 3000,
          isClosable: true,
        });
      } else {
        throw new Error(response.message || 'Failed to reset codebase');
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to reset codebase',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setIsLoading(false);
      setIsResetDialogOpen(false);
    }
  };

  return (
    <Box p={4} borderWidth="1px" borderRadius="lg" bg="white" shadow="sm">
      <Heading size="md" mb={4}>
        Codebase Operations
      </Heading>
      <Text mb={4}>
        Commit your changes to save them, or reset the codebase to its original state.
      </Text>
      <Flex gap={4}>
        <Button
          leftIcon={<FiSave />}
          colorScheme="blue"
          onClick={handleCommit}
          isLoading={isLoading}
          loadingText="Committing..."
        >
          Commit Changes
        </Button>
        <Button
          leftIcon={<FiRefreshCw />}
          colorScheme="red"
          variant="outline"
          onClick={() => setIsResetDialogOpen(true)}
          isLoading={isLoading}
          loadingText="Resetting..."
        >
          Reset Codebase
        </Button>
      </Flex>

      {/* Reset Confirmation Dialog */}
      <AlertDialog
        isOpen={isResetDialogOpen}
        leastDestructiveRef={cancelRef}
        onClose={() => setIsResetDialogOpen(false)}
      >
        <AlertDialogOverlay>
          <AlertDialogContent>
            <AlertDialogHeader fontSize="lg" fontWeight="bold">
              Reset Codebase
            </AlertDialogHeader>

            <AlertDialogBody>
              Are you sure you want to reset the codebase to its original state? This action cannot be undone.
            </AlertDialogBody>

            <AlertDialogFooter>
              <Button ref={cancelRef} onClick={() => setIsResetDialogOpen(false)}>
                Cancel
              </Button>
              <Button colorScheme="red" onClick={handleReset} ml={3} isLoading={isLoading}>
                Reset
              </Button>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialogOverlay>
      </AlertDialog>
    </Box>
  );
};

export default CodebaseOperations;