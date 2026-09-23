
package com.campus.security.repository;

import com.campus.security.model.UserSession;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface UserSessionRepository
        extends JpaRepository<UserSession, Integer> {

    Optional<UserSession> findBySessionToken(String sessionToken);


}

