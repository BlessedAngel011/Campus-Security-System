package com.campus.security.config;

import com.campus.security.security.SessionAuthenticationFilter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;

@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    @Bean
    public SecurityFilterChain securityFilterChain(
            HttpSecurity http,
            SessionAuthenticationFilter authenticationFilter)
            throws Exception {

        http
                .csrf(csrf -> csrf.disable())

                .cors(cors -> {
                })

                .addFilterBefore(
                        authenticationFilter,
                        UsernamePasswordAuthenticationFilter.class
                )

                .authorizeHttpRequests(authorize -> authorize

                        /*
                         * Public mobile login and registration.
                         */
                        .requestMatchers(
                                "/api/users/register",
                                "/api/users/login",
                                "/api/users/verify-email",
                                "/api/users/resend-verification",
                                "/api/users/forgot-password",
                                "/api/users/reset-password"
                        ).permitAll()

                        /*
                         * Public administrator website resources.
                         */
                        .requestMatchers(
                                "/",
                                "/admin",
                                "/admin/",
                                "/admin/**",
                                "/favicon.ico",
                                "/error"
                        ).permitAll()

                        /*
                         * Public administrator verification.
                         */
                        .requestMatchers(
                                "/api/admin/verify-details",
                                "/api/admin/send-code",
                                "/api/admin/confirm-code"
                        ).permitAll()

                        /*
                         * Protected administrator API.
                         */
                        .requestMatchers(
                                "/api/admin/**"
                        ).hasRole("ADMIN")

                        /*
                         * Public officer verification used when
                         * creating or verifying an officer account.
                         */
                        .requestMatchers(
                                "/api/officers/verify/**"
                        ).permitAll()

                        /*
                         * Officer profile, availability, GPS and
                         * emergency assignments.
                         *
                         * Older SECURITY and OFFICER roles are
                         * accepted for existing database records.
                         */
                        .requestMatchers(
                                "/api/officers/me",
                                "/api/officers/me/**"
                        ).hasAnyRole(
                                "ADMIN",
                                "SECURITY_OFFICER",
                                "SECURITY",
                                "OFFICER"
                        )

                        /*
                         * Administrator and officer management
                         * endpoints.
                         */
                        .requestMatchers(
                                "/api/officers",
                                "/api/officers/**"
                        ).hasAnyRole(
                                "ADMIN",
                                "SECURITY_OFFICER",
                                "SECURITY",
                                "OFFICER"
                        )

                        /*
                         * False-alert management is only available
                         * to administrators.
                         */
                        .requestMatchers(
                                "/api/false-alerts/**"
                        ).hasRole("ADMIN")

                        /*
                         * Campus locations can be viewed by all
                         * authenticated application roles.
                         */
                        .requestMatchers(
                                "/api/locations",
                                "/api/locations/**"
                        ).hasAnyRole(
                                "ADMIN",
                                "SECURITY_OFFICER",
                                "SECURITY",
                                "OFFICER",
                                "STUDENT",
                                "STAFF"
                        )

                        /*
                         * Unresolved incident reports for officers.
                         */
                        .requestMatchers(
                                "/api/incidents/officer/**"
                        ).hasAnyRole(
                                "ADMIN",
                                "SECURITY_OFFICER",
                                "SECURITY",
                                "OFFICER"
                        )

                        /*
                         * Incident status, proof and resolution
                         * operations.
                         */
                        .requestMatchers(
                                "/api/incidents/*/status",
                                "/api/incidents/*/resolve",
                                "/api/incidents/*/evidence",
                                "/api/incidents/*/evidence/**",
                                "/api/incidents/status/**"
                        ).hasAnyRole(
                                "ADMIN",
                                "SECURITY_OFFICER",
                                "SECURITY",
                                "OFFICER"
                        )

                        /*
                         * Users can report incidents and retrieve
                         * their own reports.
                         */
                        .requestMatchers(
                                "/api/incidents",
                                "/api/incidents/my-reports"
                        ).hasAnyRole(
                                "ADMIN",
                                "SECURITY_OFFICER",
                                "SECURITY",
                                "OFFICER",
                                "STUDENT",
                                "STAFF"
                        )

                        /*
                         * Officer notification endpoints.
                         */
                        .requestMatchers(
                                "/api/notifications/officer/**"
                        ).hasAnyRole(
                                "ADMIN",
                                "SECURITY_OFFICER",
                                "SECURITY",
                                "OFFICER"
                        )

                        /*
                         * User notification endpoints.
                         */
                        .requestMatchers(
                                "/api/notifications/**"
                        ).hasAnyRole(
                                "ADMIN",
                                "SECURITY_OFFICER",
                                "SECURITY",
                                "OFFICER",
                                "STUDENT",
                                "STAFF"
                        )

                        /*
                         * Students and staff can send an emergency.
                         */
                        .requestMatchers(
                                "/api/emergency/alert"
                        ).hasAnyRole(
                                "ADMIN",
                                "SECURITY_OFFICER",
                                "SECURITY",
                                "OFFICER",
                                "STUDENT",
                                "STAFF"
                        )

                        /*
                         * Officers can update emergencies assigned
                         * to them.
                         */
                        .requestMatchers(
                                "/api/emergency/*/status",
                                "/api/emergency/officer/**"
                        ).hasAnyRole(
                                "ADMIN",
                                "SECURITY_OFFICER",
                                "SECURITY",
                                "OFFICER"
                        )

                        /*
                         * Logout, current user and any remaining
                         * API require authentication.
                         */
                        .requestMatchers(
                                "/api/users/logout",
                                "/api/users/me"
                        ).authenticated()

                        .anyRequest().authenticated()
                );

        return http.build();
    }
}