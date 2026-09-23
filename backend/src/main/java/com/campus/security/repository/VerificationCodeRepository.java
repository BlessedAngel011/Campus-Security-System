package com.campus.security.repository;

import com.campus.security.model.VerificationCode;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface VerificationCodeRepository
        extends JpaRepository<VerificationCode, Integer> {

    Optional<VerificationCode> findByVerificationCode(String verificationCode);
}