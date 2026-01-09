#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SmartContextCompressor Tests
"""

import sys
from pathlib import Path
import tempfile
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from context.smart_compressor import (
    SmartContextCompressor,
    KeyInformationExtractor,
    SemanticCompressor,
    ExtractedInfo
)


def test_key_information_extraction():
    """Test key information extraction"""
    print("\n" + "=" * 60)
    print("Test 1: Key Information Extraction")
    print("=" * 60)

    kie = KeyInformationExtractor()

    # Test content
    test_content = """
    Product Name: Task Management System
    Core Features: Task creation, assignment, status tracking

    Tech Stack: Python, FastAPI, PostgreSQL, Redis

    Requirements:
    - Users can create tasks
    - Users can assign tasks to other users
    - Support task status tracking

    Decisions:
    - Use MVC architecture
    - Use JWT authentication

    Constraints:
    - API response time < 200ms
    - Support 1000 concurrent users
    """

    result = kie.extract(test_content)

    print(f"Product: {result.product}")
    print(f"Tech: {result.tech}")
    print(f"Requirements: {result.requirements}")
    print(f"Decisions: {result.decisions}")
    print(f"Constraints: {result.constraints}")

    # Verify results
    assert len(result.product) >= 1, "Should extract product name"
    assert len(result.tech) >= 1, "Should extract tech stack"
    assert len(result.requirements) >= 1, "Should extract requirements"

    print("\n[PASS] Key Information Extraction Test Passed!")


def test_semantic_compression():
    """Test semantic compression"""
    print("\n" + "=" * 60)
    print("Test 2: Semantic Compression")
    print("=" * 60)

    compressor = SemanticCompressor()

    # Test content
    original = """
    # Product Overview

    Product Name: Task Management System
    Core Features: Task creation, assignment, status tracking

    ## Tech Stack

    Using Python and FastAPI to build backend API
    Database using PostgreSQL
    Cache using Redis

    ## Functional Requirements

    Users need to be able to create tasks
    Users need to be able to assign tasks
    Users need to be able to update task status
    Users need to be able to delete tasks

    ## Architecture Decisions

    Using MVC architecture pattern
    Using JWT for authentication
    Using RESTful API design

    ## Performance Requirements

    API response time needs to be < 200ms
    System needs to support 1000 concurrent users
    Data needs to be persistently stored
    """

    compressed, stats = compressor.compress(original)

    print(f"Original length: {stats.original_length}")
    print(f"Compressed length: {stats.compressed_length}")
    print(f"Compression ratio: {stats.compression_ratio * 100:.1f}%")
    print(f"Compression method: {stats.method}")

    # Verify results
    assert stats.compressed_length < stats.original_length, "Should be shorter after compression"
    assert stats.compression_ratio < 1.0, "Compression ratio should be less than 1"

    print(f"\nCompressed content preview:\n{compressed[:500]}...")

    print("\n[PASS] Semantic Compression Test Passed!")


def test_smart_compressor():
    """Test smart context compressor"""
    print("\n" + "=" * 60)
    print("Test 3: Smart Context Compressor")
    print("=" * 60)

    compressor = SmartContextCompressor()

    # Test auto compression
    original = """
    # Task Management System

    Product Name: TaskManager Pro
    Core Features: Task management, team collaboration

    Tech Stack: Python, FastAPI, PostgreSQL

    Requirements:
    1. User registration and login
    2. Create and edit tasks
    3. Assign tasks to team members
    4. Task status tracking

    Decisions:
    - Use JWT authentication
    - Use MVC architecture

    Constraints:
    - Response time < 200ms
    - Support horizontal scaling
    """

    # Test auto mode
    compressed, stats = compressor.compress(original, method="auto")

    print(f"Auto mode compression ratio: {stats.compression_ratio * 100:.1f}%")

    # Test agent-specific compression
    compressed_backend, stats_backend = compressor.compress_for_agent(
        original, "backend-dev"
    )

    print(f"Backend agent compression ratio: {stats_backend.compression_ratio * 100:.1f}%")

    # Verify results
    assert stats.compression_ratio < 1.0, "Auto compression should be effective"
    assert stats_backend.compression_ratio < 1.0, "Agent-specific compression should be effective"

    print("\n[PASS] Smart Context Compressor Test Passed!")


def test_message_compression():
    """Test message history compression"""
    print("\n" + "=" * 60)
    print("Test 4: Message History Compression")
    print("=" * 60)

    compressor = SmartContextCompressor()

    # Create test messages
    messages = [
        {"role": "user", "content": "Develop a task management system"},
        {"role": "assistant", "content": "OK, I'll help you develop a task management system. First, let me understand the requirements..."},
        {"role": "user", "content": "Need user registration and login functionality"},
        {"role": "assistant", "content": "Got it, need user authentication. I'll add JWT authentication..."},
        {"role": "user", "content": "Also need task creation and assignment features"},
        {"role": "assistant", "content": "OK, task CRUD functionality will include create, read, update, delete..."},
        {"role": "user", "content": "Use Python and FastAPI"},
        {"role": "assistant", "content": "OK, tech stack: Python + FastAPI + PostgreSQL"},
    ]

    compressed_messages, stats = compressor.compress_messages(messages, max_tokens=1000)

    print(f"Original message count: {len(messages)}")
    print(f"Compressed message count: {len(compressed_messages)}")
    print(f"Compression ratio: {stats.compression_ratio * 100:.1f}%")

    # Verify results
    assert len(compressed_messages) <= len(messages), "Message count should not increase after compression"
    assert stats.compression_ratio > 0, "Compression ratio should be greater than 0"

    print("\n[PASS] Message History Compression Test Passed!")


def main():
    """Main test function"""
    print("\n" + "=" * 60)
    print("SmartContextCompressor Test Suite")
    print("=" * 60)

    try:
        test_key_information_extraction()
        test_semantic_compression()
        test_smart_compressor()
        test_message_compression()

        print("\n" + "=" * 60)
        print("[SUCCESS] All tests passed!")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n[FAIL] Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
