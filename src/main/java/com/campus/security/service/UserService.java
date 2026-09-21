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

import java.time.LocalDateTime;
import java.util.UUID;

@Service
public class UserService {

    private final UserRepository userRepository;
    private final RoleRepository roleRepository;
    private final CampusRepository campusRepository;
    private final UserSessionRepository sessionRepository;
    private final PasswordEncoder passwordEncoder;

    public UserService(
            UserRepository userRepository,
            RoleRepository roleRepository,
            CampusRepository campusRepository,
            UserSessionRepository sessionRepository,
            PasswordEncoder passwordEncoder) {

        this.userRepository = userRepository;
        this.roleRepository = roleRepository;
        this.campusRepository = campusRepository;
        this.sessionRepository = sessionRepository;
        this.passwordEncoder = passwordEncoder;
    }

    // Register a new user
    public User registerUser(
            String studentStaffNumber,
            String firstName,
            String lastName,
            String email,
            String phoneNumber,
            String password,
            String roleName,
            Integer campusId) {

        // Check if email already exists
        if (userRepository.existsByEmail(email)) {
            throw new RuntimeException("Email already exists.");
        }

        // Check if student/staff number already exists
        if (userRepository.existsByStudentStaffNumber(studentStaffNumber)) {
            throw new RuntimeException(
                    "Student/Staff number already exists.");
        }

        // Find the selected role
        Role role = roleRepository.findByRoleName(roleName)
                .orElseThrow(() ->
                        new RuntimeException("Role not found."));

        // Find the campus
        Campus campus = campusRepository.findById(campusId)
                .orElseThrow(() ->
                        new RuntimeException("Campus not found."));

        // Create new user
        User user = new User();

        user.setStudentStaffNumber(studentStaffNumber);
        user.setFirstName(firstName);
        user.setLastName(lastName);
        user.setEmail(email);
        user.setPhoneNumber(phoneNumber);

        // Hash the password before saving
        user.setPasswordHash(
                passwordEncoder.encode(password));

        user.setRole(role);
        user.setCampus(campus);

        user.setAccountStatus(User.AccountStatus.ACTIVE);
        user.setEmergencyButtonEnabled(true);
        user.setFalseAlertCount(0);

        return userRepository.save(user);
    }

    // Login user
    public UserSession login(
            String email,
            String password,
            String deviceId,
            String ipAddress) {

        // Find user by email
        User user = userRepository.findByEmail(email)
                .orElseThrow(() ->
                        new RuntimeException(
                                "Invalid email or password."));

        // Check account status
        if (user.getAccountStatus() != User.AccountStatus.ACTIVE) {
            throw new RuntimeException(
                    "This account is not active.");
        }

        // Check password
        if (!passwordEncoder.matches(
                password,
                user.getPasswordHash())) {

            throw new RuntimeException(
                    "Invalid email or password.");
        }

        // Create secure session token
        String sessionToken = UUID.randomUUID().toString();

        UserSession session = new UserSession();

        session.setUser(user);
        session.setSessionToken(sessionToken);
        session.setDeviceId(deviceId);
        session.setIpAddress(ipAddress);
        session.setLoginTime(LocalDateTime.now());

        // Session expires after 24 hours
        session.setExpiryTime(
                LocalDateTime.now().plusHours(24));

        session.setActive(true);

        return sessionRepository.save(session);
    }

    // Logout user
    public void logout(String sessionToken) {

        UserSession session = sessionRepository
                .findBySessionToken(sessionToken)
                .orElseThrow(() ->
                        new RuntimeException(
                                "Session not found."));

        session.setActive(false);

        sessionRepository.save(session);
    }

    // Find a user using the session token
    public User getUserFromSession(String sessionToken) {

        UserSession session = sessionRepository
                .findBySessionToken(sessionToken)
                .orElseThrow(() ->
                        new RuntimeException(
                                "Invalid session."));

        // Check whether session is active
        if (!session.getActive()) {
            throw new RuntimeException(
                    "Session has been logged out.");
        }

        // Check whether session has expired
        if (session.getExpiryTime()
                .isBefore(LocalDateTime.now())) {

            session.setActive(false);
            sessionRepository.save(session);

            throw new RuntimeException(
                    "Session has expired.");
        }

        return session.getUser();
    }

    // Check user's role
    public boolean hasRole(
            String sessionToken,
            String requiredRole) {

        User user = getUserFromSession(sessionToken);

        return user.getRole()
                .getRoleName()
                .equalsIgnoreCase(requiredRole);
    }
}