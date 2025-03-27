import React from 'react';
import { Box, Flex, Heading, Spacer, Button, useColorMode, IconButton } from '@chakra-ui/react';
import { Link as RouterLink } from 'react-router-dom';
import { FaSun, FaMoon, FaGithub } from 'react-icons/fa';

const Header: React.FC = () => {
  const { colorMode, toggleColorMode } = useColorMode();

  return (
    <Box as="header" bg="brand.500" color="white" px={4} py={2}>
      <Flex alignItems="center">
        <Heading as="h1" size="md">
          <RouterLink to="/">Codegen UI</RouterLink>
        </Heading>
        <Spacer />
        <IconButton
          aria-label="Toggle color mode"
          icon={colorMode === 'light' ? <FaMoon /> : <FaSun />}
          onClick={toggleColorMode}
          variant="ghost"
          color="white"
          _hover={{ bg: 'brand.600' }}
          mr={2}
        />
        <Button
          as="a"
          href="https://github.com/PixePerfa/codegen"
          target="_blank"
          rel="noopener noreferrer"
          leftIcon={<FaGithub />}
          variant="outline"
          color="white"
          _hover={{ bg: 'brand.600' }}
        >
          GitHub
        </Button>
      </Flex>
    </Box>
  );
};

export default Header;