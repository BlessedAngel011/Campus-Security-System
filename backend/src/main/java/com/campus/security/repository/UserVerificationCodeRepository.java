package com.campus.security.repository;

import com.campus.security.model.User;
import com.campus.security.model.UserVerificationCode;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.Optional;

public interface UserVerificationCodeRepository extends JpaRepository<UserVerificationCode, Integer> {
    Optional<UserVerificationCode> findTopByUserAndPurposeAndUsedFalseOrderByCreatedAtDesc(
            User user, UserVerificationCode.Purpose purpose);
}
