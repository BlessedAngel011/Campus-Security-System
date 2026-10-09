package com.campus.security.repository;

import com.campus.security.model.User;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface UserRepository extends JpaRepository<User, Integer> {

    Optional<User> findByStudentStaffNumber(String studentStaffNumber);

    boolean existsByStudentStaffNumber(String studentStaffNumber);

    Optional<User> findByEmailIgnoreCase(String email);

    boolean existsByEmailIgnoreCase(String email);

    Optional<User> findByPersonalEmailIgnoreCase(String personalEmail);

    boolean existsByPersonalEmailIgnoreCase(String personalEmail);
}