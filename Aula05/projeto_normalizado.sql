-- Projeto Normalizado (3FN) - Clínica Médica "HealthTech"
-- Substitui a tabela única Relatorio_Geral_Consultas por 4 entidades.

DROP TABLE IF EXISTS Consulta CASCADE;
DROP TABLE IF EXISTS Medico CASCADE;
DROP TABLE IF EXISTS Paciente CASCADE;
DROP TABLE IF EXISTS Convenio CASCADE;

CREATE TABLE Convenio (
    id_convenio    INTEGER PRIMARY KEY,
    nome_convenio  VARCHAR(100) NOT NULL
);

CREATE TABLE Paciente (
    cpf_paciente       CHAR(11) PRIMARY KEY,
    nome_paciente      TEXT NOT NULL,
    telefone_paciente  VARCHAR(15)
);

CREATE TABLE Medico (
    crm_medico             VARCHAR(20) PRIMARY KEY,
    nome_medico            TEXT NOT NULL,
    especialidade_medico   VARCHAR(50)
);

CREATE TABLE Consulta (
    id_consulta       INTEGER PRIMARY KEY,
    data_consulta     DATE NOT NULL,
    hora_consulta     TIME NOT NULL,
    valor_consulta    NUMERIC(10,2),
    fk_cpf_paciente   CHAR(11) NOT NULL REFERENCES Paciente(cpf_paciente),
    fk_crm_medico     VARCHAR(20) NOT NULL REFERENCES Medico(crm_medico),
    fk_id_convenio    INTEGER REFERENCES Convenio(id_convenio)
);
