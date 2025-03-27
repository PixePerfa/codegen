// Project types
export interface Project {
  id: string;
  name: string;
  language: string;
  path: string;
  initialized?: boolean;
}

// File types
export interface File {
  path: string;
  content?: string;
  is_source: boolean;
  symbols?: Symbol[];
}

// Symbol types
export interface Symbol {
  name: string;
  type: string;
  file_path?: string;
  line?: number;
  column?: number;
}

// Class types
export interface Class extends Symbol {
  methods: Method[];
}

// Method types
export interface Method {
  name: string;
  line: number;
  column: number;
}

// Function types
export interface Function extends Symbol {
  parameters: string[];
}

// Search types
export interface SearchMatch {
  path: string;
  line_number: number;
  lines: string;
  submatches: {
    match: string;
    start: number;
    end: number;
  }[];
}

export interface SearchResult {
  matches: SearchMatch[];
}

// Transform types
export interface TransformOperation {
  operation: string;
  params: any;
}

export interface TransformResult {
  status: string;
  result: string;
}

// Batch operation types
export interface BatchOperation {
  operation: string;
  files: string[];
  params: any;
}

export interface BatchResult {
  status: string;
  results: {
    file: string;
    result: string;
  }[];
}

// Analysis types
export interface AnalysisRequest {
  type: string;
  target?: string;
  params?: any;
}

export interface AnalysisResult {
  status: string;
  result: any;
}

// Dependency types
export interface Dependency {
  source: {
    name: string;
    type: string;
    file_path: string;
  };
  target: {
    name: string;
    type: string;
    file_path: string;
  };
}

// Import types
export interface Import {
  module: string;
  name: string;
  alias?: string;
  is_relative: boolean;
}

// Git operation types
export interface GitOperation {
  operation: string;
  params: any;
}

export interface GitResult {
  status: string;
  result: any;
}

// Metrics types
export interface CodeMetrics {
  total_files: number;
  total_symbols: number;
  total_classes: number;
  total_functions: number;
  lines_of_code: number;
}