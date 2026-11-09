/**
 * Helioz AI - Curated Academy Courses
 * Pre-compiled, instant-load foundational courses with vetted lectures and quizzes.
 */

export const CURATED_COURSES = [
  {
    id: "featured-c-systems",
    course_title: "Systems Programming & Memory in C",
    category: "Computer Science",
    level: "Foundational",
    description: "Architectural overview of C, compiled binary execution, pointer arithmetic, and heap memory allocation.",
    modules: [
      {
        topic: "1. Compilation Model & Machine Architecture",
        video_url: "https://www.youtube.com/watch?v=KJgsSFOSQv0",
        video_title: "C Programming Tutorial 1 - Introduction & How C Works",
        quiz: [
          {
            question: "Which component in C translates source code into machine-executable binary code?",
            options: ["Preprocessor", "Compiler", "Linker", "Operating System"],
            correct_answer: "Compiler"
          },
          {
            question: "What is the return type of the main() function by standard C convention?",
            options: ["void", "int", "float", "char"],
            correct_answer: "int"
          }
        ]
      },
      {
        topic: "2. Control Flow, Branching & Loop Constructs",
        video_url: "https://www.youtube.com/watch?v=kbc_5aGg44w",
        video_title: "Control Structures in C - If Else & Loops Explained",
        quiz: [
          {
            question: "Which loop is guaranteed to execute at least once regardless of condition evaluation?",
            options: ["while loop", "for loop", "do-while loop", "nested loop"],
            correct_answer: "do-while loop"
          },
          {
            question: "What statement is used to immediately exit a switch block?",
            options: ["continue", "break", "return", "exit"],
            correct_answer: "break"
          }
        ]
      },
      {
        topic: "3. Pointers, Memory Addresses & Heap Allocation",
        video_url: "https://www.youtube.com/watch?v=zuegQmMdy8M",
        video_title: "Pointers in C / C++ [Full Course]",
        quiz: [
          {
            question: "Which operator is used to obtain the physical memory address of a variable in C?",
            options: ["*", "&", "->", "%"],
            correct_answer: "&"
          },
          {
            question: "Which standard library function dynamically allocates memory on the heap without zero-initialization?",
            options: ["calloc()", "malloc()", "realloc()", "free()"],
            correct_answer: "malloc()"
          }
        ]
      }
    ]
  },
  {
    id: "featured-eng-math",
    course_title: "Engineering Mathematics: Linear Systems & Matrices",
    category: "Mathematics",
    level: "Intermediate",
    description: "Core linear algebra, determinant geometry, matrix invertibility, and spectral decomposition.",
    modules: [
      {
        topic: "1. Linear Algebra: Matrices & Determinants",
        video_url: "https://www.youtube.com/watch?v=kYB8IZa5AuE",
        video_title: "Essence of Linear Algebra - Matrix Multiplication as Composition",
        quiz: [
          {
            question: "What is the determinant of an identity matrix of any dimension?",
            options: ["0", "-1", "1", "Undefined"],
            correct_answer: "1"
          },
          {
            question: "If the determinant of square matrix A is 0, the matrix is classified as:",
            options: ["Orthogonal", "Singular (Non-invertible)", "Symmetric", "Diagonal"],
            correct_answer: "Singular (Non-invertible)"
          }
        ]
      },
      {
        topic: "2. Eigenvalues and Eigenvectors",
        video_url: "https://www.youtube.com/watch?v=PFDu9oVAE-g",
        video_title: "Eigenvalues and Eigenvectors - 3Blue1Brown",
        quiz: [
          {
            question: "In the fundamental equation Av = λv, what does the scalar λ represent?",
            options: ["Eigenvector", "Eigenvalue", "Trace", "Matrix Rank"],
            correct_answer: "Eigenvalue"
          }
        ]
      },
      {
        topic: "3. Multivariable Calculus: Partial Derivatives & Gradients",
        video_url: "https://www.youtube.com/watch?v=AXqhWeUEtQU",
        video_title: "Gradients and Partial Derivatives Visualized",
        quiz: [
          {
            question: "When taking a partial derivative with respect to x, all other variables are treated as:",
            options: ["Zero", "Independent Variables", "Constants", "Composite Functions"],
            correct_answer: "Constants"
          }
        ]
      }
    ]
  },
  {
    id: "featured-dsa",
    course_title: "Data Structures & Algorithmic Complexity",
    category: "Algorithms",
    level: "Core",
    description: "Asymptotic notation, amortized array operations, linked representations, and tree traversals.",
    modules: [
      {
        topic: "1. Asymptotic Complexity and Big-O Notation",
        video_url: "https://www.youtube.com/watch?v=D6xkbGLQesk",
        video_title: "Introduction to Big O Notation and Time Complexity",
        quiz: [
          {
            question: "What is the worst-case time complexity of binary search on a sorted array?",
            options: ["O(1)", "O(log n)", "O(n)", "O(n log n)"],
            correct_answer: "O(log n)"
          },
          {
            question: "Which complexity class grows faster as n approaches infinity?",
            options: ["O(n log n)", "O(n^2)", "O(2^n)", "O(n!)"],
            correct_answer: "O(n!)"
          }
        ]
      },
      {
        topic: "2. Dynamic Arrays vs Linked List Pointer Traversal",
        video_url: "https://www.youtube.com/watch?v=F8xQ45sXUvU",
        video_title: "Arrays vs Linked Lists - Deep Dive",
        quiz: [
          {
            question: "What is the random access time complexity for an element at index i in an array?",
            options: ["O(1)", "O(n)", "O(log n)", "O(i)"],
            correct_answer: "O(1)"
          }
        ]
      }
    ]
  }
];
