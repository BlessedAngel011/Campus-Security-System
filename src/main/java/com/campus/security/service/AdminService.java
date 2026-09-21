package com.campus.security.service;

import com.campus.security.model.Administrator;
import com.campus.security.model.VerificationCode;
import com.campus.security.repository.AdministratorRepository;
import com.campus.security.repository.VerificationCodeRepository;

import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.Random;

@Service
public class AdminService {

    private final AdministratorRepository administratorRepository;
    private final VerificationCodeRepository verificationCodeRepository;

    public AdminService(
            AdministratorRepository administratorRepository,
            VerificationCodeRepository verificationCodeRepository) {

        this.administratorRepository = administratorRepository;
        this.verificationCodeRepository = verificationCodeRepository;
    }


    // =========================================================
    // 1. VERIFY ADMINISTRATOR DETAILS
    // =========================================================

    public Administrator verifyAdminDetails(
            String employeeNumber,
            String universityEmail) {

        // Find administrator using employee number
        Administrator admin =
                administratorRepository
                        .findByEmployeeNumber(employeeNumber)
                        .orElseThrow(() ->
                                new RuntimeException(
                                        "Administrator employee number not found."
                                )
                        );

        // Check that the university email matches
        if (!admin.getUniversityEmail()
                .equalsIgnoreCase(universityEmail)) {

            throw new RuntimeException(
                    "University email does not match the employee number."
            );
        }

        return admin;
    }


    // =========================================================
    // 2. GENERATE VERIFICATION CODE
    // =========================================================

    public VerificationCode generateVerificationCode(
            String employeeNumber,
            String universityEmail) {

        // Verify administrator details first
        Administrator admin =
                verifyAdminDetails(
                        employeeNumber,
                        universityEmail
                );

        // Generate a random 6-digit verification code
        String code =
                String.format(
                        "%06d",
                        new Random().nextInt(1000000)
                );

        // Create a new verification code object
        VerificationCode verificationCode =
                new VerificationCode();

        // Connect the code to the administrator
        verificationCode.setAdministrator(admin);

        // Store the 6-digit code
        verificationCode.setVerificationCode(code);

        // Code expires after 10 minutes
        verificationCode.setExpiresAt(
                LocalDateTime.now().plusMinutes(10)
        );

        // Code has not been used yet
        verificationCode.setUsed(false);

        // Set creation time
        verificationCode.setCreatedAt(
                LocalDateTime.now()
        );

        // Save the verification code in MySQL
        VerificationCode savedCode =
                verificationCodeRepository.save(
                        verificationCode
                );

        return savedCode;
    }


    // =========================================================
    // 3. CONFIRM VERIFICATION CODE
    // =========================================================

    public Administrator confirmVerificationCode(
            String employeeNumber,
            String code) {

        // Find the administrator
        Administrator admin =
                administratorRepository
                        .findByEmployeeNumber(employeeNumber)
                        .orElseThrow(() ->
                                new RuntimeException(
                                        "Administrator not found."
                                )
                        );

        // Find the verification code
        VerificationCode verificationCode =
                verificationCodeRepository
                        .findByVerificationCode(code)
                        .orElseThrow(() ->
                                new RuntimeException(
                                        "Invalid verification code."
                                )
                        );

        // Check that the code belongs to this administrator
        if (!verificationCode
                .getAdministrator()
                .getAdminId()
                .equals(admin.getAdminId())) {

            throw new RuntimeException(
                    "Verification code does not belong to this administrator."
            );
        }

        // Check whether the code has already been used
        if (verificationCode.getUsed()) {

            throw new RuntimeException(
                    "Verification code has already been used."
            );
        }

        // Check whether the code has expired
        if (verificationCode
                .getExpiresAt()
                .isBefore(LocalDateTime.now())) {

            throw new RuntimeException(
                    "Verification code has expired."
            );
        }

        // Mark the verification code as used
        verificationCode.setUsed(true);

        // Save the updated verification code
        verificationCodeRepository.save(
                verificationCode
        );

        // Mark administrator as VERIFIED
        admin.setVerificationStatus(
                Administrator.VerificationStatus.VERIFIED
        );

        // Save the verified administrator
        return administratorRepository.save(admin);
    }
}