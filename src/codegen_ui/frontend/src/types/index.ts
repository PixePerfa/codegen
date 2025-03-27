// Project types
export interface Project {
  id: string;
  name: string;
  language: string;
  path: string;
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