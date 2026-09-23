
package com.campus.security.service;

import com.campus.security.model.Campus;
import com.campus.security.model.Role;
import com.campus.security.model.User;
import com.campus.security.model.UserSession;
import com.campus.security.repository.CampusRepository;
import com.campus.security.repository.RoleRepository;
import com.campus.security.repository.UserRepository;
import com.campus.security.repository.UserSessionRepository;

import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.UUID;

@Service
public class UserService {

    private final UserRepository userRepository;
    private final UserSessionRepository userSessionRepository;
    private final RoleRepository roleRepository;
    private final CampusRepository campusRepository;
    private final PasswordEncoder passwordEncoder;

    public UserService(
            UserRepository userRepository,
            UserSessionRepository userSessionRepository,
            RoleRepository roleRepository,
            CampusRepository campusRepository,
            PasswordEncoder passwordEncoder) {

        this.userRepository = userRepository;
        this.userSessionRepository = userSessionRepository;
        this.roleRepository = roleRepository;
        this.campusRepository = campusRepository;
        this.passwordEncoder = passwordEncoder;
    }

    @Transactional
    public User registerUser(
            String username,
            String password,
            String firstName,
            String lastName,
            String phoneNumber,
            String roleName,
            Integer campusId) {

        // Check whether student/staff number already exists
        if (userRepository.existsByStudentStaffNumber(username)) {
            throw new RuntimeException(
                    "Student/staff number already exists."
            );
        }

        // Find the requested role
        Role role = roleRepository.findByRoleNameIgnoreCase(roleName)
                .orElseGet(() -> roleRepository.findAll().stream()
                        .filter(item -> normaliseRole(item.getRoleName())
                                .equals(normaliseRole(roleName)))
                        .findFirst()
                        .orElseThrow(() -> new RuntimeException(
                                "Role not found: " + roleName)));

        // Find the campus
        Campus campus = campusRepository.findById(campusId)
                .orElseThrow(() ->
                        new RuntimeException(
                                "Campus not found: " + campusId
                        )
                );

        User user = new User();

        user.setStudentStaffNumber(username);

        user.setFirstName(firstName);
        user.setLastName(lastName);
        user.setPhoneNumber(phoneNumber);


        user.setEmail(username + "@ufh.ac.za");

        user.setPasswordHash(
                passwordEncoder.encode(password)
        );

        user.setRole(role);
        user.setCampus(campus);

        user.setAccountStatus(User.AccountStatus.ACTIVE);
        user.setEmergencyButtonEnabled(true);
        user.setFalseAlertCount(0);

        return userRepository.save(user);
    }

    private String normaliseRole(String roleName) {
        return roleName == null ? "" : roleName.trim()
                .replace(" ", "_")
                .replace("-", "_")
                .toUpperCase();
    }


    /**
     * Login a user and create a secure session.
     */
    @Transactional
    public UserSession login(
            String username,
            String password,
            String deviceId,
            String ipAddress) {

        User user = userRepository
                .findByStudentStaffNumber(username)
                .orElseThrow(() ->
                        new RuntimeException(
                                "Invalid student/staff number or password."
                        )
                );

        // Check account status
        if (user.getAccountStatus() != User.AccountStatus.ACTIVE) {
            throw new RuntimeException(
                    "User account is not active."
            );
        }

        // Check password
        if (!passwordEncoder.matches(
                password,
                user.getPasswordHash())) {

            throw new RuntimeException(
                    "Invalid student/staff number or password."
            );
        }

        // Generate secure session token
        String sessionToken = UUID.randomUUID().toString();

        UserSession session = new UserSession();

        session.setUser(user);
        session.setSessionToken(sessionToken);
        session.setDeviceId(deviceId);
        session.setIpAddress(ipAddress);

        session.setLoginTime(LocalDateTime.now());

        // Keep the mobile user signed in for 30 days.
        session.setExpiryTime(
                LocalDateTime.now().plusDays(30)
        );

        session.setActive(true);

        return userSessionRepository.save(session);
    }


    /**
     * Logout a user using their session token.
     */
    @Transactional
    public void logout(String sessionToken) {

        UserSession session = userSessionRepository
                .findBySessionToken(sessionToken)
                .orElseThrow(() ->
                        new RuntimeException(
                                "Session not found."
                        )
                );

        session.setActive(false);

        userSessionRepository.save(session);
    }


    /**
     * Get the user associated with a session token.
     */
    @Transactional
    public User getUserFromSession(String sessionToken) {

        UserSession session = userSessionRepository
                .findBySessionToken(sessionToken)
                .orElseThrow(() ->
                        new RuntimeException(
                                "Session not found."
                        )
                );

        // Check whether session is active
        if (!Boolean.TRUE.equals(session.getActive())) {

            throw new RuntimeException(
                    "Session is no longer active."
            );
        }

        // Check whether session has expired
        if (session.getExpiryTime()
                .isBefore(LocalDateTime.now())) {

            session.setActive(false);
            userSessionRepository.save(session);

            throw new RuntimeException(
                    "Session has expired."
            );
        }

        return session.getUser();
    }
}

