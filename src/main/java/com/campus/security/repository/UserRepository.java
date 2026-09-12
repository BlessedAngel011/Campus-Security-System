package com.campus.security.repository;

import com.campus.security.model.User;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface UserRepository extends JpaRepository<User, Integer> {

    Optional<User> findByEmail(String email);

    Optional<User> findByStudentStaffNumber(String studentStaffNumber);

    boolean existsByEmail(String email);

    boolean existsByStudentStaffNumber(String studentStaffNumber);
}