package com.campus.security.security;

import com.campus.security.model.User;
import com.campus.security.model.UserSession;
import com.campus.security.repository.UserSessionRepository;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.time.LocalDateTime;
import java.util.Collections;

@Component
public class SessionAuthenticationFilter
        extends OncePerRequestFilter {

    private final UserSessionRepository sessionRepository;

    public SessionAuthenticationFilter(
            UserSessionRepository sessionRepository) {

        this.sessionRepository = sessionRepository;
    }

    @Override
    protected void doFilterInternal(
            HttpServletRequest request,
            HttpServletResponse response,
            FilterChain filterChain)
            throws ServletException, IOException {

        String authorization =
                request.getHeader("Authorization");

        // Check whether Authorization header exists
        if (authorization != null
                && authorization.startsWith("Bearer ")) {

            String token =
                    authorization.substring(7);

            UserSession session =
                    sessionRepository
                            .findBySessionToken(token)
                            .orElse(null);

            // Check that session exists
            if (session != null) {

                // Check session is active
                if (session.getActive()
                        && session.getExpiryTime()
                        .isAfter(LocalDateTime.now())) {

                    User user = session.getUser();

                    String roleName =
                            user.getRole().getRoleName();

                    /*
                     * Spring Security expects roles
                     * in the form ROLE_ADMIN.
                     */
                    String authority =
                            "ROLE_" +
                                    roleName
                                            .toUpperCase()
                                            .replace(" ", "_");

                    UsernamePasswordAuthenticationToken
                            authentication =
                            new UsernamePasswordAuthenticationToken(
                                    user,
                                    null,
                                    Collections.singletonList(
                                            new SimpleGrantedAuthority(
                                                    authority)));

                    SecurityContextHolder
                            .getContext()
                            .setAuthentication(
                                    authentication);
                }
            }
        }

        filterChain.doFilter(request, response);
    }
}